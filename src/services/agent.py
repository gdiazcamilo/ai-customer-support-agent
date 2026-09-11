"""Defines the agent logic and configuration. Process the prompt and return the result"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field

from strands import Agent
from strands.models import BedrockModel
from strands.types.content import Messages

from agentcore_config import AGENTCORE_SETTINGS
from functions.api.logging_utils import log_event
from services.agent_hooks import STRANDS_HOOKS
from services.prompt import load_system_prompt
from tools.executor import (
    ToolExecutionContext,
)
from tools.strands_adapters import STRANDS_TOOLS, build_request_state

logger = logging.getLogger()

logger.setLevel(AGENTCORE_SETTINGS.log_level)


SYSTEM_PROMPT = load_system_prompt()


MAX_AGENT_ITERATIONS = 5

THINKING_BLOCK_PATTERN = re.compile(
    r"<thinking>.*?</thinking>",
    flags=re.DOTALL | re.IGNORECASE,
)


class AgentMaxIterationsError(Exception):
    pass


@dataclass
class AgentResult:
    answer: str
    retrieved_sources: list[str] = field(default_factory=list)


def extract_public_answer(text: str) -> str:
    return THINKING_BLOCK_PATTERN.sub("", text).strip()


def run_agent(
    prompt: str,
    request_id: str | None = None,
    execution_context: ToolExecutionContext | None = None,
    conversation_history: Messages | None = None,
) -> AgentResult:
    execution_context = execution_context or ToolExecutionContext(request_id=request_id)

    request_state = build_request_state(
        request_id=execution_context.request_id,
        confirmed_actions=execution_context.confirmed_actions,
    )

    log_event(
        logger,
        logging.INFO,
        "agent_started",
        request_id=request_id,
        model_id=AGENTCORE_SETTINGS.bedrock_model_id,
    )

    model = BedrockModel(
        model_id=AGENTCORE_SETTINGS.bedrock_model_id,
        temperature=0,
        max_tokens=200,
        streaming=False,
        guardrail_id=AGENTCORE_SETTINGS.bedrock_guardrail_id,
        guardrail_version=AGENTCORE_SETTINGS.bedrock_guardrail_version,
        guardrail_trace="enabled",
    )

    agent = Agent(
        model=model,
        tools=STRANDS_TOOLS,
        hooks=STRANDS_HOOKS,
        system_prompt=SYSTEM_PROMPT,
        messages=list(conversation_history or []),
        callback_handler=None,
    )

    result = agent(
        prompt,
        invocation_state={
            "request_state": request_state,
        },
        limits={"turns": MAX_AGENT_ITERATIONS},
    )

    if result.stop_reason == "limit_turns":
        log_event(
            logger,
            logging.ERROR,
            "agent_max_iterations_exceeded",
            request_id=request_id,
            max_iterations=MAX_AGENT_ITERATIONS,
        )

        raise AgentMaxIterationsError(
            f"Agent exceeded {MAX_AGENT_ITERATIONS} iterations"
        )

    raw_answer = str(result)
    public_answer = extract_public_answer(raw_answer)

    summary = result.metrics.get_summary()

    usage = summary["accumulated_usage"]
    metrics = summary["accumulated_metrics"]

    log_event(
        logger,
        logging.INFO,
        "agent_completed",
        request_id=request_id,
        response_length=len(public_answer),
        cycles=summary["total_cycles"],
        duration_ms=round(summary["total_duration"] * 1000),
        model_latency_ms=metrics["latencyMs"],
        input_tokens=usage["inputTokens"],
        output_tokens=usage["outputTokens"],
        total_tokens=usage["totalTokens"],
    )

    return AgentResult(
        answer=public_answer,
        retrieved_sources=sorted(result.state["retrieved_sources"]),
    )
