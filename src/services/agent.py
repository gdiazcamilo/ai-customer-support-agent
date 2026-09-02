from __future__ import annotations

import logging
from dataclasses import dataclass, field

import boto3
from strands import Agent
from strands.models import BedrockModel
from strands.types.content import Messages

from agentcore_config import AGENTCORE_SETTINGS
from functions.api.logging_utils import log_event
from tools.executor import (
    ToolExecutionContext,
)
from tools.strands_adapters import STRANDS_TOOLS, build_request_state

logger = logging.getLogger()

logger.setLevel(AGENTCORE_SETTINGS.log_level)

bedrock_runtime = boto3.client("bedrock-runtime")


SYSTEM_PROMPT = """
You are a concise customer support assistant.

- Answer clearly and briefly.
- Use tools when you need external information.
- Do not invent information.
- Do not claim that an action happened unless a tool successfully performed it.
- When using retrieved company documentation, only answer with information supported by the retrieved content.
- If the retrieved content does not contain enough information to answer, say that you do not have enough information.
- Distinguish general policy questions from requests about specific entities:
  use policy search for general shipping, return, or warranty questions;
  use order lookup only when the user is asking about a specific existing order.
- Do not imply that you can perform future research or follow-up actions
  unless an available tool actually supports that action.
- When answering from retrieved company documentation, do not add facts,
  explanations, assumptions, or general knowledge that are not explicitly
  supported by the retrieved content.
- Do not include source URLs, document links, or citations in your answer.
  Source attribution is handled separately by the application.
- Use the conversation history provided in the messages to answer follow-up questions.
- When previous messages are available, do not claim that you cannot remember or access the previous conversation.
- If the user asks what they were discussing, summarize the relevant previous messages.
"""


MAX_AGENT_ITERATIONS = 5


class AgentMaxIterationsError(Exception):
    pass


@dataclass
class AgentResult:
    answer: str
    retrieved_sources: list[str] = field(default_factory=list)


def run_agent(
    prompt: str,
    request_id: str | None = None,
    execution_context: ToolExecutionContext | None = None,
    conversation_history: Messages | None = None,
) -> AgentResult:
    execution_context = execution_context or ToolExecutionContext(request_id=request_id)

    request_state = build_request_state(
        request_id="req-123", confirmed_actions=execution_context.confirmed_actions
    )

    log_event(
        logger,
        logging.INFO,
        "agent_started",
        request_id=request_id,
        model_id=AGENTCORE_SETTINGS.bedrock_model_id,
    )

    model = BedrockModel(
        model_id=AGENTCORE_SETTINGS.bedrock_model_id, temperature=0, max_tokens=200
    )

    agent = Agent(
        model=model,
        tools=STRANDS_TOOLS,
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

    answer = str(result)

    log_event(
        logger,
        logging.INFO,
        "agent_completed",
        request_id=request_id,
        response_length=len(answer),
    )

    return AgentResult(
        answer=answer,
        retrieved_sources=sorted(result.state["retrieved_sources"]),
    )
