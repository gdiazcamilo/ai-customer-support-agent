import pytest

from services.agent import (
    AgentMaxIterationsError,
    execute_tool_request,
    run_agent,
)
from tools.executor import ToolExecutionContext


def test_unknown_tool_is_returned_as_tool_error():
    tool_use = {
        "toolUseId": "tool-test-1",
        "name": "delete_everything",
        "input": {},
    }

    result, sources = execute_tool_request(
        tool_use,
        request_id="request-test-1",
        execution_context=ToolExecutionContext(),
    )

    assert sources == []
    assert result["toolUseId"] == "tool-test-1"
    assert result["status"] == "error"
    assert "unknown tool" in result["content"][0]["text"].lower()


def test_invalid_tool_input_is_returned_as_tool_error():
    tool_use = {
        "toolUseId": "tool-test-2",
        "name": "get_order",
        "input": {
            "order_id": 123,
        },
    }

    result, sources = execute_tool_request(
        tool_use,
        request_id="request-test-2",
        execution_context=ToolExecutionContext(),
    )

    assert sources == []
    assert result["toolUseId"] == "tool-test-2"
    assert result["status"] == "error"
    assert "order_id" in result["content"][0]["text"]


def test_unexpected_tool_exception_propagates(monkeypatch):
    def broken_execute_tool(*args, **kwargs):
        raise RuntimeError("unexpected internal bug")

    monkeypatch.setattr(
        "services.agent.execute_tool",
        broken_execute_tool,
    )

    tool_use = {
        "toolUseId": "tool-test-3",
        "name": "get_order",
        "input": {
            "order_id": "ORD-123",
        },
    }

    with pytest.raises(
        RuntimeError,
        match="unexpected internal bug",
    ):
        execute_tool_request(
            tool_use,
            request_id="request-test-3",
            execution_context=ToolExecutionContext(),
        )


def test_agent_stops_after_max_iterations(monkeypatch):
    tool_counter = 0

    def fake_converse(**kwargs):
        nonlocal tool_counter
        tool_counter += 1

        return {
            "stopReason": "tool_use",
            "output": {
                "message": {
                    "role": "assistant",
                    "content": [
                        {
                            "toolUse": {
                                "toolUseId": f"tool-{tool_counter}",
                                "name": "get_order",
                                "input": {
                                    "order_id": "ORD-123",
                                },
                            }
                        }
                    ],
                }
            },
            "usage": {
                "inputTokens": 10,
                "outputTokens": 5,
                "totalTokens": 15,
            },
            "metrics": {
                "latencyMs": 10,
            },
        }

    monkeypatch.setattr(
        "services.agent.bedrock_runtime.converse",
        fake_converse,
    )

    with pytest.raises(AgentMaxIterationsError):
        run_agent(
            "Where is order ORD-123?",
            request_id="request-test-4",
        )
