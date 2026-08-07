from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from aws_lambda_typing.events import APIGatewayProxyEventV2

from functions.api.config import SETTINGS
from functions.api.responses import error_response, json_response, success_response
from functions.api.service import get_health_status, process_chat
from functions.api.validation import (
    ValidationError,
    parse_json_body,
    validate_chat_payload,
)


def route_request(
    event: APIGatewayProxyEventV2,
    request_id: str,
) -> dict[str, Any]:
    method = event.get("requestContext", {}).get("http", {}).get("method")
    path = event.get("rawPath")

    if method == "GET" and path == "/health":
        return handle_health()

    if method == "POST" and path == "/chat":
        return handle_chat(
            event=event,
            request_id=request_id,
        )

    return handle_unknown_route(
        method=method,
        path=path,
        request_id=request_id,
    )


def handle_health() -> dict[str, Any]:
    health_data = get_health_status(environment=SETTINGS.environment, service_name=SETTINGS.service_name)

    return json_response(
        status_code=200,
        body=health_data,
    )


def handle_chat(
    event: dict[str, Any],
    request_id: str,
) -> dict[str, Any]:
    try:
        payload = parse_json_body(event)
        message = validate_chat_payload(payload)
    except ValidationError as exc:
        return error_response(
            status_code=400,
            code=exc.code,
            message=exc.message,
            request_id=request_id,
        )

    chat_data = process_chat(message=message, request_id=request_id)

    return success_response(
        data=chat_data,
        request_id=request_id,
    )


def handle_unknown_route(
    method: str | None,
    path: str | None,
    request_id: str,
) -> dict[str, Any]:
    known_paths = {
        "/health": {"GET"},
        "/chat": {"POST"},
    }

    if path in known_paths and method not in known_paths[path]:
        return error_response(
            status_code=405,
            code="METHOD_NOT_ALLOWED",
            message="The HTTP method is not allowed for this route.",
            request_id=request_id,
        )

    return error_response(
        status_code=404,
        code="ROUTE_NOT_FOUND",
        message="The requested route does not exist.",
        request_id=request_id,
    )
