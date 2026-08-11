from __future__ import annotations

import logging
import os
from typing import Any

# Local-development defaults.
# In AgentCore Runtime these values come from EnvironmentVariables
# defined in CloudFormation.
os.environ.setdefault(
    "SUPPORT_JOBS_QUEUE_URL",
    "https://sqs.us-east-1.amazonaws.com/214078205303/ai-customer-support-jobs-dev",
)
os.environ.setdefault(
    "BEDROCK_MODEL_ID",
    "amazon.nova-micro-v1:0",
)
os.environ.setdefault(
    "KNOWLEDGE_BASE_ID",
    "3GVCFXAJNA",
)
os.environ.setdefault(
    "AGENTCORE_MEMORY_ID",
    "ai_customer_support_memory_dev-a6pPuz84yT",
)


# These imports must happen after the local environment defaults above,
# because SETTINGS is loaded at import time.
from bedrock_agentcore.runtime import BedrockAgentCoreApp

from functions.api.config import SETTINGS
from services.agent import run_agent
from services.memory import load_conversation, save_message

logging.basicConfig(
    level=SETTINGS.log_level,
    format="%(message)s",
)


app = BedrockAgentCoreApp()


@app.entrypoint
def invoke_agent(payload: dict[str, Any]) -> dict[str, Any]:
    prompt = payload.get("prompt")

    if not isinstance(prompt, str) or not prompt.strip():
        raise ValueError("prompt must be a non-empty string")

    request_id = payload.get("request_id")
    conversation_id = payload.get("conversation_id")

    if conversation_id is not None and (
        not isinstance(conversation_id, str) or not conversation_id.strip()
    ):
        raise ValueError("conversation_id must be a non-empty string")

    # We do not have customer authentication yet, so for this
    # learning phase all conversations belong to one test actor.
    actor_id = "support-user"

    conversation_history: list[dict[str, Any]] = []

    if conversation_id is not None:
        conversation_history = load_conversation(
            actor_id=actor_id,
            conversation_id=conversation_id,
        )

    result = run_agent(
        prompt,
        request_id=request_id,
        conversation_history=conversation_history,
    )

    # Persist the completed conversational turn only after the agent
    # has successfully produced a response.
    if conversation_id is not None:
        save_message(
            actor_id=actor_id,
            conversation_id=conversation_id,
            role="USER",
            text=prompt,
        )

        save_message(
            actor_id=actor_id,
            conversation_id=conversation_id,
            role="ASSISTANT",
            text=result.answer,
        )

    return {
        "answer": result.answer,
        "retrieved_sources": result.retrieved_sources,
    }


if __name__ == "__main__":
    app.run()
