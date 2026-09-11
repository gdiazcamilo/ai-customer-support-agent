from __future__ import annotations

import json
from typing import Any

from local_environment import configure_local_environment

configure_local_environment()

from strands import Agent
from strands.models import BedrockModel

from agentcore_config import AGENTCORE_SETTINGS
from services.agent import SYSTEM_PROMPT
from services.agent_hooks import STRANDS_HOOKS
from tools.strands_adapters import STRANDS_TOOLS, build_request_state


class InspectingBedrockModel(BedrockModel):
    def format_request(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        request = super().format_request(*args, **kwargs)

        print("\n=== BEDROCK CONVERSE REQUEST ===")
        print(json.dumps(request, indent=2, default=str))
        print("=== END REQUEST ===\n")

        return request


model = InspectingBedrockModel(
    model_id="amazon.nova-micro-v1:0",
    temperature=0,
    max_tokens=200,
    streaming=False,
    guardrail_id=AGENTCORE_SETTINGS.bedrock_guardrail_id,
    guardrail_version=AGENTCORE_SETTINGS.bedrock_guardrail_version,
    guardrail_trace="enabled",
)

original_converse = model.client.converse


def inspecting_converse(**kwargs: Any) -> dict[str, Any]:
    response = original_converse(**kwargs)

    print("\n=== RAW BEDROCK CONVERSE RESPONSE ===")
    print(json.dumps(response, indent=2, default=str))
    print("=== END RESPONSE ===\n")

    return response


model.client.converse = inspecting_converse

agent = Agent(
    model=model,
    tools=STRANDS_TOOLS,
    system_prompt=SYSTEM_PROMPT,
    callback_handler=None,
    hooks=STRANDS_HOOKS,
)

result = agent(
    "What is the return policy?",
    invocation_state={"request_state": build_request_state()},
)

print("\n=== FINAL RESULT ===")
print(result)
