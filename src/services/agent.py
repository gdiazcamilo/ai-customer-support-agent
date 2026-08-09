from __future__ import annotations

import logging
import re
from typing import Any

import boto3

from functions.api.config import SETTINGS
from functions.api.logging_utils import log_event
from tools.executor import (
    InvalidToolInputError,
    ToolExecutionContext,
    UnknownToolError,
    execute_tool,
)
from tools.registry import BEDROCK_TOOLS

logger = logging.getLogger()
logger.setLevel(SETTINGS.log_level)

bedrock_runtime = boto3.client("bedrock-runtime")


SYSTEM_PROMPT = """
You are a concise customer support assistant.

- Answer clearly and briefly.
- Use tools when you need external information.
- Do not invent information.
- Do not claim that an action happened unless a tool successfully performed it.
"""


MAX_AGENT_ITERATIONS = 5


class AgentMaxIterationsError(Exception):
    pass


def run_agent(
    message: str,
    request_id: str | None = None,
    execution_context: ToolExecutionContext | None = None,
) -> str:
    execution_context = execution_context or ToolExecutionContext()
    log_event(
        logger,
        logging.INFO,
        "agent_started",
        request_id=request_id,
        model_id=SETTINGS.bedrock_model_id,
    )

    messages: list[dict[str, Any]] = [
        {
            "role": "user",
            "content": [
                {
                    "text": message,
                }
            ],
        }
    ]

    for iteration in range(1, MAX_AGENT_ITERATIONS + 1):
        response = bedrock_runtime.converse(
            modelId=SETTINGS.bedrock_model_id,
            system=[
                {
                    "text": SYSTEM_PROMPT,
                }
            ],
            messages=messages,
            toolConfig={
                "tools": BEDROCK_TOOLS,
            },
            inferenceConfig={
                "maxTokens": 200,
                "temperature": 0,
            },
        )

        usage = response["usage"]
        metrics = response["metrics"]

        log_event(
            logger,
            logging.INFO,
            "agent_iteration_completed",
            request_id=request_id,
            iteration=iteration,
            model_id=SETTINGS.bedrock_model_id,
            stop_reason=response["stopReason"],
            input_tokens=usage["inputTokens"],
            output_tokens=usage["outputTokens"],
            total_tokens=usage["totalTokens"],
            latency_ms=metrics["latencyMs"],
        )

        assistant_message = response["output"]["message"]

        messages.append(assistant_message)

        stop_reason = response["stopReason"]

        if stop_reason == "end_turn":
            final_text = extract_text(assistant_message)

            log_event(
                logger,
                logging.INFO,
                "agent_completed",
                request_id=request_id,
                iterations=iteration,
                response_length=len(final_text),
            )

            return final_text

        if stop_reason == "tool_use":
            tool_result_message = execute_tool_requests(
                assistant_message,
                request_id=request_id,
                execution_context=execution_context,
            )

            messages.append(tool_result_message)
            continue

        raise RuntimeError(f"Unsupported Bedrock stop reason: {stop_reason}")

    log_event(
        logger,
        logging.ERROR,
        "agent_max_iterations_exceeded",
        request_id=request_id,
        max_iterations=MAX_AGENT_ITERATIONS,
    )
    raise AgentMaxIterationsError(f"Agent exceeded {MAX_AGENT_ITERATIONS} iterations")


def execute_tool_requests(
    assistant_message: dict[str, Any],
    request_id: str | None = None,
    execution_context: ToolExecutionContext | None = None,
) -> dict[str, Any]:

    result_blocks = []

    for block in assistant_message["content"]:
        if "toolUse" not in block:
            continue

        tool_use = block["toolUse"]
        tool_result = execute_tool_request(
            tool_use, request_id=request_id, execution_context=execution_context
        )

        result_blocks.append(
            {
                "toolResult": tool_result,
            }
        )

    if not result_blocks:
        raise RuntimeError("Bedrock returned tool_use but no toolUse blocks")

    return {
        "role": "user",
        "content": result_blocks,
    }


def execute_tool_request(
    tool_use: dict[str, Any],
    request_id: str | None = None,
    execution_context: ToolExecutionContext | None = None,
) -> dict[str, Any]:
    log_event(
        logger,
        logging.INFO,
        "tool_requested",
        request_id=request_id,
        tool_name=tool_use["name"],
        tool_use_id=tool_use["toolUseId"],
    )

    try:
        result = execute_tool(
            tool_use["name"],
            tool_use["input"],
            context=execution_context,
        )
    except (UnknownToolError, InvalidToolInputError) as exc:
        log_event(
            logger,
            logging.WARNING,
            "tool_request_rejected",
            request_id=request_id,
            tool_name=tool_use.get("name"),
            tool_use_id=tool_use.get("toolUseId"),
            error_type=type(exc).__name__,
        )

        return {
            "toolUseId": tool_use["toolUseId"],
            "content": [
                {
                    "text": str(exc),
                }
            ],
            "status": "error",
        }

    if result.success:
        log_event(
            logger,
            logging.INFO,
            "tool_execution_completed",
            request_id=request_id,
            tool_name=tool_use["name"],
            tool_use_id=tool_use["toolUseId"],
            status="success",
        )

        return {
            "toolUseId": tool_use["toolUseId"],
            "content": [
                {
                    "json": result.content,
                }
            ],
            "status": "success",
        }

    log_event(
        logger,
        logging.WARNING,
        "tool_execution_completed",
        request_id=request_id,
        tool_name=tool_use["name"],
        tool_use_id=tool_use["toolUseId"],
        status="error",
    )

    return {
        "toolUseId": tool_use["toolUseId"],
        "content": [
            {
                "text": str(result.content),
            }
        ],
        "status": "error",
    }


def extract_text(
    assistant_message: dict[str, Any],
) -> str:
    text = "".join(
        block["text"] for block in assistant_message["content"] if "text" in block
    )

    text = re.sub(
        r"<thinking>.*?</thinking>",
        "",
        text,
        flags=re.DOTALL,
    )

    return text.strip()
