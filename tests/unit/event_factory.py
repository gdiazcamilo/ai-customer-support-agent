import json
from typing import Any


def make_api_event(
    method: str = "GET",
    path: str = "/health",
    body: dict[str, Any] | str | None = None,
    request_id: str = "api-request-id",
    is_base64_encoded: bool = False,
    headers: dict[str, str] | None = None,
) -> dict[str, Any]:
    if isinstance(body, dict):
        serialized_body = json.dumps(body)
    else:
        serialized_body = body

    return {
        "version": "2.0",
        "routeKey": f"{method} {path}",
        "rawPath": path,
        "headers": headers or {},
        "requestContext": {
            "requestId": request_id,
            "http": {
                "method": method,
                "path": path,
            },
        },
        "body": serialized_body,
        "isBase64Encoded": is_base64_encoded,
    }
