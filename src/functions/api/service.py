from typing import Any

from .config import SETTINGS

STATIC_CHAT_RESPONSE = "The support agent is not connected to AI yet."


def get_health_status(
    service_name: str,
    environment: str,
) -> dict[str, str]:
    return {
        "status": "ok",
        "service": service_name,
        "environment": environment,
    }


def process_chat(message: str) -> dict[str, str]:
    return {
        "message": message,
        "response": STATIC_CHAT_RESPONSE,
    }