GET_ORDER_TOOL = {
    "toolSpec": {
        "name": "get_order",
        "description": (
            "Retrieve information about a customer order by its order ID. "
            "Use this tool when the user asks about the status or delivery "
            "of a specific order."
        ),
        "inputSchema": {
            "json": {
                "type": "object",
                "properties": {
                    "order_id": {
                        "type": "string",
                        "description": ("The order identifier, for example ORD-123."),
                    }
                },
                "required": ["order_id"],
                "additionalProperties": False,
            }
        },
    }
}


GET_CUSTOMER_TOOL = {
    "toolSpec": {
        "name": "get_customer",
        "description": (
            "Retrieve information about a customer by customer ID. "
            "Use this tool when the user asks about a specific customer's "
            "name, account, or customer tier."
        ),
        "inputSchema": {
            "json": {
                "type": "object",
                "properties": {
                    "customer_id": {
                        "type": "string",
                        "description": (
                            "The customer identifier, for example CUST-123."
                        ),
                    }
                },
                "required": ["customer_id"],
            }
        },
    }
}
