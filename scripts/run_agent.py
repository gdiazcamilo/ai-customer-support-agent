from services.agent import run_agent
from tools.executor import ToolExecutionContext, build_confirmed_action
from tools.orders import ORDERS

context = ToolExecutionContext(
    confirmed_actions=frozenset(
        {
            build_confirmed_action(
                "cancel_order",
                {"order_id": "ORD-456"},
            )
        }
    ),
)
print(
    run_agent(
        "Cancel order ORD-456",
        execution_context=context,
    )
)

print(
    run_agent(
        "Cancel order ORD-456",
        execution_context=context,
    )
)


print(ORDERS)
