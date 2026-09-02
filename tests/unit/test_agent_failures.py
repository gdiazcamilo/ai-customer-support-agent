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
