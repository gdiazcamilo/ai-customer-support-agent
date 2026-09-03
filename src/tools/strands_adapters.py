from __future__ import annotations

from typing import Any

from strands import ToolContext, tool

from tools.erros import InvalidToolInputError, UnknownToolError
from tools.executor import (
    ConfirmedAction,
    ToolExecutionContext,
    ToolExecutionResult,
    execute_tool,
)


def build_request_state(
    request_id: str | None = None,
    confirmed_actions: frozenset[ConfirmedAction] | None = None,
) -> dict[str, Any]:
    return {
        "request_id": request_id,
        "retrieved_sources": set(),
        "confirmed_actions": confirmed_actions or frozenset(),
    }


def get_request_state(
    tool_context: ToolContext,
) -> dict[str, Any]:
    request_state = tool_context.invocation_state.get("request_state")

    if not isinstance(request_state, dict):
        raise TypeError("Strands request_state is missing")

    return request_state


def build_tool_execution_context(
    tool_context: ToolContext,
) -> ToolExecutionContext:
    request_state = get_request_state(tool_context)

    confirmed_actions = request_state.get(
        "confirmed_actions",
        frozenset(),
    )

    if not isinstance(confirmed_actions, frozenset):
        raise TypeError("confirmed_actions must be a frozenset")

    return ToolExecutionContext(
        request_id=request_state.get("request_id"),
        confirmed_actions=confirmed_actions,
    )


def execute_application_tool(
    *,
    name: str,
    tool_input: dict[str, Any],
    tool_context: ToolContext,
) -> ToolExecutionResult | str:
    try:
        return execute_tool(
            name,
            tool_input,
            context=build_tool_execution_context(tool_context),
        )
    except (UnknownToolError, InvalidToolInputError) as exc:
        return str(exc)


@tool(context=True)
def get_order(
    order_id: str,
    tool_context: ToolContext,
) -> dict | str:
    """
    Retrieve information about a specific customer order by order ID.

    Use this tool only for the status, shipment, delivery, or details of
    a particular existing order. Do not use it for general shipping
    methods, shipping times, or company shipping policies.

    Args:
        order_id: The order identifier, for example ORD-123.
    """

    result = execute_application_tool(
        name="get_order",
        tool_input={"order_id": order_id},
        tool_context=tool_context,
    )

    if isinstance(result, str):
        return result

    return result.content


@tool(context=True)
def get_customer(
    customer_id: str,
    tool_context: ToolContext,
) -> dict | str:
    """
    Retrieve information about a specific customer by customer ID.

    Use this tool only to get customer name, tier or account.
    Do not use it for other general customer concerns.

    Args:
        customer_id: The customer_id identifier, for example CUST-123
    """

    result = execute_application_tool(
        name="get_customer",
        tool_input={"customer_id": customer_id},
        tool_context=tool_context,
    )

    if isinstance(result, str):
        return result

    return result.content


@tool(context=True)
def cancel_order(
    order_id: str,
    tool_context: ToolContext,
) -> dict | str:
    """
    Cancel a specific existing customer order.

    Use this tool only when the user explicitly asks to cancel
    a specific order.

    Args:
        order_id: The order identifier, for example ORD-456
    """

    result = execute_application_tool(
        name="cancel_order",
        tool_input={"order_id": order_id},
        tool_context=tool_context,
    )

    if isinstance(result, str):
        return result

    return result.content


@tool(context=True)
def search_policies(
    query: str,
    tool_context: ToolContext,
) -> dict | str:
    """
    Search company policies and customer-support documentation.

    Use this tool for general questions about returns, warranties,
    shipping methods, shipping times, international shipping, and other
    company policies. Use it even when the user does not explicitly use
    the word 'policy'. Do not use it to look up the status of a specific order.
    """

    result = execute_application_tool(
        name="search_policies",
        tool_input={"query": query},
        tool_context=tool_context,
    )

    if isinstance(result, str):
        return result

    if not result.success or not isinstance(result.content, dict):
        return result.content

    results = result.content["results"]

    request_state = get_request_state(tool_context)
    retrieved_sources = request_state["retrieved_sources"]

    if not isinstance(retrieved_sources, set):
        raise TypeError("retrieved_sources must be a set")

    for item in results:
        source = item.get("source")

        if source:
            retrieved_sources.add(source)

    return {
        "results": [
            {
                "text": item["text"],
                "score": item.get("score"),
            }
            for item in results
        ]
    }


STRANDS_TOOLS: list[Any] = [
    get_order,
    get_customer,
    cancel_order,
    search_policies,
]
