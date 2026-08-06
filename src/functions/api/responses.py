import json
from typing import Any

JSON_HEADERS = {
    "content-type": "application/json",
}


def json_response(
    status_code: int,
    body: dict[str, Any],
) -> dict[str, Any]:
    """
    Build a response compatible with API Gateway HTTP API
    Lambda proxy integration.
    """
    return {
        "statusCode": status_code,
        "headers": JSON_HEADERS.copy(),
        "body": json.dumps(body),
    }


def success_response(
    data: dict[str, Any],
    request_id: str,
    status_code: int = 200,
) -> dict[str, Any]:
    return json_response(
        status_code=status_code,
        body={
            "data": data,
            "request_id": request_id,
        },
    )


def error_response(
    status_code: int,
    code: str,
    message: str,
    request_id: str,
) -> dict[str, Any]:
    return json_response(
        status_code=status_code,
        body={
            "error": {
                "code": code,
                "message": message,
            },
            "request_id": request_id,
        },
    )
