from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from tools.customers import CustomerNotFoundError, get_customer
from tools.knowledge import search_policies
from tools.orders import (
    OrderCannotBeCancelledError,
    OrderNotFoundError,
    cancel_order,
    get_order,
)

ToolCallable = Callable[..., dict[str, Any]]


@dataclass(frozen=True)
class ToolDefinition:
    name: str
    function: ToolCallable
    properties: dict[str, dict[str, Any]]
    required: tuple[str, ...]
    expected_errors: tuple[type[Exception], ...]
    side_effects: bool = False
    requires_confirmation: bool = False
    pass_request_id: bool = False


GET_ORDER = ToolDefinition(
    name="get_order",
    function=get_order,
    properties={
        "order_id": {
            "type": "string",
        }
    },
    required=("order_id",),
    expected_errors=(OrderNotFoundError,),
)


GET_CUSTOMER = ToolDefinition(
    name="get_customer",
    function=get_customer,
    properties={
        "customer_id": {
            "type": "string",
        }
    },
    required=("customer_id",),
    expected_errors=(CustomerNotFoundError,),
)

CANCEL_ORDER = ToolDefinition(
    name="cancel_order",
    function=cancel_order,
    properties={
        "order_id": {
            "type": "string",
        }
    },
    required=("order_id",),
    expected_errors=(
        OrderNotFoundError,
        OrderCannotBeCancelledError,
    ),
    side_effects=True,
    requires_confirmation=True,
)

SEARCH_POLICIES = ToolDefinition(
    name="search_policies",
    function=search_policies,
    properties={
        "query": {
            "type": "string",
        }
    },
    required=("query",),
    expected_errors=(),
    pass_request_id=True,
)

TOOL_REGISTRY = {
    tool.name: tool
    for tool in (
        GET_ORDER,
        GET_CUSTOMER,
        CANCEL_ORDER,
        SEARCH_POLICIES,
    )
}
