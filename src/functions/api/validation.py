import base64
import binascii
import json
from dataclasses import dataclass
from typing import Any

MAX_MESSAGE_LENGTH = 4_000
ALLOWED_CHAT_FIELDS = {"message"}

@dataclass
class ValidationError(Exception):
    code: str
    message: str


def parse_json_body(event: dict[str, Any]) -> dict[str, Any]:
    body = event.get("body")

    if body is None or body == "":
        raise ValidationError(
            code="INVALID_JSON",
            message="The request body must contain valid JSON.",
        )

    if event.get("isBase64Encoded", False):
        try:
            body = base64.b64decode(body, validate=True).decode("utf-8")
        except (binascii.Error, UnicodeDecodeError):
            raise ValidationError(
                code="INVALID_JSON",
                message="The request body must contain valid JSON.",
            )

    try:
        payload = json.loads(body)
    except (json.JSONDecodeError, TypeError):
        raise ValidationError(
            code="INVALID_JSON",
            message="The request body must contain valid JSON.",
        )

    if not isinstance(payload, dict):
        raise ValidationError(
            code="INVALID_REQUEST",
            message="The request body must be a JSON object.",
        )

    return payload


def validate_chat_payload(payload: dict[str, Any]) -> str:
    unknown_fields = set(payload) - ALLOWED_CHAT_FIELDS

    if unknown_fields:
        raise ValidationError(
            code="INVALID_REQUEST",
            message="The request contains unsupported fields.",
        )

    if "message" not in payload:
        raise ValidationError(
            code="INVALID_REQUEST",
            message="The field 'message' is required.",
        )

    message = payload["message"]

    if not isinstance(message, str):
        raise ValidationError(
            code="INVALID_REQUEST",
            message="The field 'message' must be a string.",
        )

    normalized_message = message.strip()

    if not normalized_message:
        raise ValidationError(
            code="INVALID_REQUEST",
            message="The field 'message' must not be empty.",
        )

    if len(normalized_message) > MAX_MESSAGE_LENGTH:
        raise ValidationError(
            code="INVALID_REQUEST",
            message=(
                "The field 'message' must not exceed "
                f"{MAX_MESSAGE_LENGTH} characters."
            ),
        )

    return normalized_message