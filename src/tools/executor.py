from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Union

from tools.idempotency import (
    build_idempotency_key,
    get_processed_result,
    save_processed_result,
)
from tools.registry import TOOL_REGISTRY, ToolDefinition


class UnknownToolError(Exception):
    pass


class InvalidToolInputError(Exception):
    pass


@dataclass
class ToolExecutionResult:
    success: bool
    content: Union[dict[str, Any], str]
    confirmation_required: bool = False


@dataclass(frozen=True)
class ConfirmedAction:
    tool_name: str
    arguments: tuple[tuple[str, Any], ...]


@dataclass(frozen=True)
class ToolExecutionContext:
    confirmed_actions: frozenset[ConfirmedAction] = field(default_factory=frozenset)
    request_id: str | None = None


def build_confirmed_action(
    tool_name: str,
    tool_input: dict[str, Any],
) -> ConfirmedAction:
    return ConfirmedAction(
        tool_name=tool_name,
        arguments=tuple(sorted(tool_input.items())),
    )


def execute_tool(
    name: str,
    tool_input: dict[str, Any],
    context: ToolExecutionContext,
) -> ToolExecutionResult:
    try:
        definition = TOOL_REGISTRY[name]
    except KeyError as exc:
        raise UnknownToolError(f"Unknown tool: {name}") from exc

    validated_input = validate_tool_input(
        definition,
        tool_input,
    )

    requested_action = build_confirmed_action(
        name,
        validated_input,
    )

    if (
        definition.requires_confirmation
        and requested_action not in context.confirmed_actions
    ):
        return ToolExecutionResult(
            success=False,
            content=(
                f"Explicit confirmation is required before executing "
                f"{name} with these arguments."
            ),
            confirmation_required=True,
        )

    idempotency_key = None

    if definition.side_effects:
        idempotency_key = build_idempotency_key(
            tool_name=name,
            arguments=validated_input,
        )

        previous_result = get_processed_result(idempotency_key)

        if previous_result is not None:
            return ToolExecutionResult(
                success=True,
                content=previous_result,
            )

    try:
        function_arguments = dict(validated_input)

        if definition.pass_request_id:
            function_arguments["request_id"] = context.request_id

        result = definition.function(**function_arguments)
    except definition.expected_errors as exc:
        return ToolExecutionResult(
            success=False,
            content=str(exc),
        )

    if idempotency_key is not None:
        save_processed_result(
            idempotency_key,
            result,
        )

    return ToolExecutionResult(
        success=True,
        content=result,
    )
