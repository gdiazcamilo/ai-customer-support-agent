from tools.executor import execute_tool

print(execute_tool("get_order", {"order_id": "ORD-123"}))

print(execute_tool("get_order", {"order_id": 123}))
