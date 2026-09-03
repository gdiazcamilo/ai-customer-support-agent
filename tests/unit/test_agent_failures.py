import pytest

from services.agent import AgentMaxIterationsError, run_agent


class FakeResult:
    stop_reason = "limit_turns"
    state = {"retrieved_sources": set()}

    def __str__(self) -> str:
        return ""


class FakeAgent:
    def __init__(self, *args, **kwargs):
        pass

    def __call__(self, *args, **kwargs):
        return FakeResult()


class SuccessfulFakeResult:
    stop_reason = "completed"
    state = {"retrieved_sources": set()}

    class Metrics:
        @staticmethod
        def get_summary():
            return {
                "accumulated_usage": {
                    "inputTokens": 10,
                    "outputTokens": 20,
                    "totalTokens": 30,
                },
                "accumulated_metrics": {"latencyMs": 100},
                "total_cycles": 1,
                "total_duration": 0.1,
            }

    metrics = Metrics()

    def __str__(self) -> str:
        return "<thinking>Internal reasoning that must not be returned.</thinking> Your order has shipped."


class SuccessfulFakeAgent:
    def __init__(self, *args, **kwargs):
        pass

    def __call__(self, *args, **kwargs):
        return SuccessfulFakeResult()


def test_agent_stops_after_max_iterations(monkeypatch):
    monkeypatch.setattr(
        "services.agent.Agent",
        FakeAgent,
    )

    with pytest.raises(AgentMaxIterationsError):
        run_agent(
            "Where is order ORD-123?",
            request_id="request-test-4",
        )


def test_agent_response_removes_thinking_tags(monkeypatch):
    monkeypatch.setattr("services.agent.Agent", SuccessfulFakeAgent)

    result = run_agent("Where is order ORD-123?", request_id="request-test-5")

    assert result.answer == "Your order has shipped."
    assert "<thinking>" not in result.answer
