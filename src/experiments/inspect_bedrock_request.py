from __future__ import annotations

import json
import os
from typing import Any

os.environ.setdefault(
    "BEDROCK_MODEL_ID",
    "amazon.nova-micro-v1:0",
)
os.environ.setdefault(
    "KNOWLEDGE_BASE_ID",
    "unused-for-this-experiment",
)
os.environ.setdefault(
    "AGENTCORE_MEMORY_ID",
    "unused-for-this-experiment",
)

from strands import Agent
from strands.models import BedrockModel

from services.agent import SYSTEM_PROMPT
from tools.strands_adapters import STRANDS_TOOLS


class InspectingBedrockModel(BedrockModel):
    def format_request(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        request = super().format_request(*args, **kwargs)

        # print("\n=== BEDROCK CONVERSE REQUEST ===")
        # print(json.dumps(request, indent=2, default=str))
        # print("=== END REQUEST ===\n")

        return request


model = InspectingBedrockModel(
    model_id="amazon.nova-micro-v1:0",
    temperature=0,
    max_tokens=200,
    streaming=False,
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
)

result = agent("What is the status of order ORD-123?")

print("\n=== FINAL RESULT ===")
print(result)
