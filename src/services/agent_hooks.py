import logging

from strands.hooks import (
    AfterModelCallEvent,
    AfterToolCallEvent,
    AfterToolsEvent,
    BeforeToolCallEvent,
    HookCallback,
    HookProvider,
)

from agentcore_config import AGENTCORE_SETTINGS
from functions.api.logging_utils import log_event

logger = logging.getLogger()

logger.setLevel(AGENTCORE_SETTINGS.log_level)


def log_before_tool_call(event: BeforeToolCallEvent) -> None:
    request_state = event.invocation_state["request_state"]

    log_event(
        logger,
        logging.INFO,
        "tool_requested",
        request_id=request_state.get("request_id"),
        tool_name=event.tool_use["name"],
        tool_use_id=event.tool_use["toolUseId"],
    )


def log_after_tool_call(event: AfterToolCallEvent) -> None:
    request_state = event.invocation_state["request_state"]

    log_event(
        logger,
        logging.INFO if event.exception is None else logging.WARNING,
        "tool_execution_completed",
        request_id=request_state.get("request_id"),
        tool_name=event.tool_use["name"],
        tool_use_id=event.tool_use["toolUseId"],
        execution_status="completed" if event.exception is None else "exception",
    )


def log_after_model_call(event: AfterModelCallEvent) -> None:
    request_state = event.invocation_state["request_state"]

    if event.exception is not None:
        log_event(
            logger,
            logging.ERROR,
            "model_call_completed",
            request_id=request_state.get("request_id"),
            execution_status="error",
            error_type=type(event.exception).__name__,
        )
        return

    stop_response = event.stop_response

    if stop_response is None:
        log_event(
            logger,
            logging.WARNING,
            "model_call_completed",
            request_id=request_state.get("request_id"),
            execution_status="completed_without_response",
        )
        return

    usage = stop_response.message["metadata"]["usage"]

    log_event(
        logger,
        logging.INFO,
        "model_call_completed",
        request_id=request_state.get("request_id"),
        execution_status="completed",
        stop_reason=stop_response.stop_reason,
        input_tokens=usage["inputTokens"],
        output_tokens=usage["outputTokens"],
        total_tokens=usage["totalTokens"],
    )


def add_contextual_grounding(event: AfterToolsEvent) -> None:
    print("add_contextual_grounding hook started")
    request_state = event.invocation_state["request_state"]

    # use `pop` to prevent reuse in a later tool call of the same invocation.
    grounding_context = request_state.pop(
        "pending_grounding_context",
        None,
    )

    if grounding_context is None:
        return

    event.message["content"].extend(
        [
            {
                "guardContent": {
                    "text": {
                        "text": grounding_context["query"],
                        "qualifiers": ["query"],
                    }
                }
            },
            {
                "guardContent": {
                    "text": {
                        "text": grounding_context["source"],
                        "qualifiers": ["grounding_source"],
                    }
                }
            },
        ]
    )
    print("add_contextual_grounding finished")


STRANDS_HOOKS: list[HookCallback | HookProvider] = [
    log_before_tool_call,
    log_after_tool_call,
    log_after_model_call,
    add_contextual_grounding,
]
