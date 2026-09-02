import pytest

from tools.executor import (
    ConfirmedAction,
    ToolExecutionContext,
    ToolExecutionResult,
)
from tools.strands_adapters import (
    build_request_state,
    build_tool_execution_context,
    cancel_order,
    get_order,
    search_policies,
)


class FakeToolContext:
    def __init__(self, request_state):
        self.invocation_state = {
            "request_state": request_state,
        }


def test_build_request_state():
    confirmed_actions = frozenset(
        {
            ConfirmedAction(
                tool_name="cancel_order",
                arguments=(("order_id", "ORD-123"),),
            )
        }
    )

    request_state = build_request_state(
        request_id="request-123",
        confirmed_actions=confirmed_actions,
    )

    assert request_state == {
        "request_id": "request-123",
        "retrieved_sources": set(),
        "confirmed_actions": confirmed_actions,
    }


def test_build_tool_execution_context_uses_request_state():
    confirmed_actions = frozenset(
        {
            ConfirmedAction(
                tool_name="cancel_order",
                arguments=(("order_id", "ORD-123"),),
            )
        }
    )
    tool_context = FakeToolContext(
        build_request_state(
            request_id="request-123",
            confirmed_actions=confirmed_actions,
        )
    )

    context = build_tool_execution_context(tool_context)

    assert context == ToolExecutionContext(
        request_id="request-123",
        confirmed_actions=confirmed_actions,
    )


def test_get_order_passes_request_id_to_executor(monkeypatch):
    captured_context = None

    def fake_execute_tool(name, tool_input, *, context):
        nonlocal captured_context
        captured_context = context
        assert name == "get_order"
        assert tool_input == {"order_id": "ORD-123"}
        return ToolExecutionResult(
            success=True,
            content={"order_id": "ORD-123"},
        )

    monkeypatch.setattr(
        "tools.strands_adapters.execute_tool",
        fake_execute_tool,
    )
    tool_context = FakeToolContext(build_request_state(request_id="request-123"))

    result = get_order(order_id="ORD-123", tool_context=tool_context)

    assert result == {"order_id": "ORD-123"}
    assert captured_context == ToolExecutionContext(request_id="request-123")


def test_cancel_order_preserves_confirmed_actions(monkeypatch):
    confirmed_actions = frozenset(
        {
            ConfirmedAction(
                tool_name="cancel_order",
                arguments=(("order_id", "ORD-123"),),
            )
        }
    )
    captured_context = None

    def fake_execute_tool(name, tool_input, *, context):
        nonlocal captured_context
        captured_context = context
        assert name == "cancel_order"
        assert tool_input == {"order_id": "ORD-123"}
        return ToolExecutionResult(
            success=True,
            content={"order_id": "ORD-123", "status": "cancelled"},
        )

    monkeypatch.setattr(
        "tools.strands_adapters.execute_tool",
        fake_execute_tool,
    )
    tool_context = FakeToolContext(
        build_request_state(
            request_id="request-123",
            confirmed_actions=confirmed_actions,
        )
    )

    result = cancel_order(order_id="ORD-123", tool_context=tool_context)

    assert result == {"order_id": "ORD-123", "status": "cancelled"}
    assert captured_context == ToolExecutionContext(
        request_id="request-123",
        confirmed_actions=confirmed_actions,
    )


def test_search_policies_collects_sources_but_hides_them_from_model_result(
    monkeypatch,
):
    def fake_execute_tool(name, tool_input, *, context):
        assert name == "search_policies"
        assert tool_input == {"query": "How long does shipping take?"}
        return ToolExecutionResult(
            success=True,
            content={
                "results": [
                    {
                        "text": (
                            "Standard shipping normally takes 5 to 7 business days."
                        ),
                        "score": 0.91,
                        "source": "s3://bucket/shipping-policy.md",
                    }
                ]
            },
        )

    monkeypatch.setattr(
        "tools.strands_adapters.execute_tool",
        fake_execute_tool,
    )
    request_state = build_request_state(request_id="request-123")
    tool_context = FakeToolContext(request_state)

    result = search_policies(
        query="How long does shipping take?",
        tool_context=tool_context,
    )

    assert result == {
        "results": [
            {
                "text": "Standard shipping normally takes 5 to 7 business days.",
                "score": 0.91,
            }
        ]
    }
    assert request_state["retrieved_sources"] == {"s3://bucket/shipping-policy.md"}


def test_unexpected_executor_error_propagates(monkeypatch):
    def fake_execute_tool(name, tool_input, *, context):
        raise RuntimeError("executor failed")

    monkeypatch.setattr(
        "tools.strands_adapters.execute_tool",
        fake_execute_tool,
    )
    tool_context = FakeToolContext(build_request_state(request_id="request-123"))

    with pytest.raises(RuntimeError, match="executor failed"):
        get_order(order_id="ORD-123", tool_context=tool_context)
