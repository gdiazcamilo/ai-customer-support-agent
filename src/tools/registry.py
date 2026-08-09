from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

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
        "Retrieve information about a specific customer order by its order ID. "
        "Use this tool only when the user is asking about the status, shipment, "
        "delivery, or details of a particular existing order. "
        "Do not use this tool for general questions about shipping methods, "
        "shipping times, or company shipping policies."
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

SEARCH_POLICIES = ToolDefinition(
    name="search_policies",
    description=(
        "Search company policies and support documentation. "
        "Use this tool for general questions about returns, warranties, "
        "shipping methods, shipping times, international shipping, and other "
        "company policies. Use it even when the user does not explicitly use "
        "the word 'policy'. Do not use it to look up the status of a specific order."
    ),
    function=search_policies,
    properties={
        "query": {
            "type": "string",
            "description": (
                "The user's question or topic to search for in company "
                "policies and support documentation."
            ),
        }
    },
    required=("query",),
    expected_errors=(),
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


BEDROCK_TOOLS = [tool.bedrock_spec() for tool in TOOL_REGISTRY.values()]
