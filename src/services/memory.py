from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import boto3

from agentcore_config import AGENTCORE_SETTINGS

memory_client = boto3.client("bedrock-agentcore")


def save_message(
    *,
    actor_id: str,
    conversation_id: str,
    role: str,
    text: str,
) -> None:
    memory_client.create_event(
        memoryId=AGENTCORE_SETTINGS.memory_id,
        actorId=actor_id,
        sessionId=conversation_id,
        eventTimestamp=datetime.now(timezone.utc),
        payload=[
            {
                "conversational": {
                    "role": role,
                    "content": {
                        "text": text,
                    },
                }
            }
        ],
        extractionMode="SKIP",
    )


def load_conversation(
    *,
    actor_id: str,
    conversation_id: str,
) -> list[dict[str, Any]]:
    response = memory_client.list_events(
        memoryId=AGENTCORE_SETTINGS.memory_id,
        actorId=actor_id,
        sessionId=conversation_id,
        includePayloads=True,
    )

    events = sorted(
        response.get("events", []),
        key=lambda event: event["eventTimestamp"],
    )

    messages = []

    for event in events:
        for payload in event.get("payload", []):
            conversational = payload.get("conversational")

            if not conversational:
                continue

            role = conversational.get("role")
            text = conversational.get("content", {}).get("text")

            if role not in {"USER", "ASSISTANT"} or not text:
                continue

            messages.append(
                {
                    "role": "user" if role == "USER" else "assistant",
                    "content": [{"text": text}],
                }
            )

    return messages
