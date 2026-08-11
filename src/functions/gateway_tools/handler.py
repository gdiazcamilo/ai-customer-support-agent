from tools.orders import get_order


def handler(event, context):
    tool_name = context.client_context.custom["bedrockAgentCoreToolName"]
    tool_name = tool_name.split("___", 1)[-1]

    if tool_name == "get_order":
        return get_order(**event)

    raise ValueError(f"Unknown tool: {tool_name}")
