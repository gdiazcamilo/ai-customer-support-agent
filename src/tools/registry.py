from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from tools.customers import CustomerNotFoundError, get_customer
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
    description: str
    function: ToolCallable
    properties: dict[str, dict[str, Any]]
    required: tuple[str, ...]
    expected_errors: tuple[type[Exception], ...]
    side_effects: bool = False
    requires_confirmation: bool = False

    def bedrock_spec(self) -> dict[str, Any]:
        return {
            "toolSpec": {
                "name": self.name,
                "description": self.description,
                "inputSchema": {
                    "json": {
                        "type": "object",
                        "properties": self.properties,
                        "required": list(self.required),
                    }
                },
            }
        }


GET_ORDER = ToolDefinition(
    name="get_order",
    description=(
        "Retrieve information about a customer order by its order ID. "
        "Use this tool when the user asks about the status or delivery "
        "of a specific order."
    ),
    function=get_order,
    properties={
        "order_id": {
            "type": "string",
            "description": "The order identifier, for example ORD-123.",
        }
    },
    required=("order_id",),
    expected_errors=(OrderNotFoundError,),
)


GET_CUSTOMER = ToolDefinition(
    name="get_customer",
    description=(
        "Retrieve information about a customer by customer ID. "
        "Use this tool when the user asks about a specific customer's "
        "name, account, or customer tier."
    ),
    function=get_customer,
    properties={
        "customer_id": {
            "type": "string",
            "description": "The customer identifier, for example CUST-123.",
        }
    },
    required=("customer_id",),
    expected_errors=(CustomerNotFoundError,),
)

CANCEL_ORDER = ToolDefinition(
    name="cancel_order",
    description=(
        "Cancel an existing customer order. "
        "Use this tool only when the user explicitly asks to cancel "
        "a specific order."
    ),
    function=cancel_order,
    properties={
        "order_id": {
            "type": "string",
            "description": "The order identifier, for example ORD-456.",
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


TOOL_REGISTRY = {
    tool.name: tool
    for tool in (
        GET_ORDER,
        GET_CUSTOMER,
        CANCEL_ORDER,
    )
}


BEDROCK_TOOLS = [tool.bedrock_spec() for tool in TOOL_REGISTRY.values()]
