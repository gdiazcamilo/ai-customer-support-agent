import json

from src.functions.api.router import route_request
from src.functions.api.service import STATIC_CHAT_RESPONSE

from .event_factory import make_api_event


def body(response: dict[str, object]) -> dict[str, object]:
    return json.loads(response["body"])  # type: ignore[arg-type]


def test_get_health_returns_200_and_health_fields() -> None:
    response = route_request(make_api_event("GET", "/health"), request_id="req-1")

    payload = body(response)
    assert response["statusCode"] == 200
    assert payload["status"] == "ok"
    assert "service" in payload
    assert "environment" in payload


def test_post_chat_with_valid_input_returns_200() -> None:
    response = route_request(
        make_api_event("POST", "/chat", body={"message": "hello"}),
        request_id="req-1",
    )

    assert response["statusCode"] == 200


def test_post_chat_success_includes_normalized_message_and_static_response() -> None:
    response = route_request(
        make_api_event("POST", "/chat", body={"message": "  hello  "}),
        request_id="req-1",
    )

    assert body(response) == {
        "data": {
            "message": "hello",
            "response": STATIC_CHAT_RESPONSE,
        },
        "request_id": "req-1",
    }


def test_post_chat_invalid_json_returns_400_invalid_json() -> None:
    response = route_request(
        make_api_event("POST", "/chat", body="{"),
        request_id="req-1",
    )

    assert response["statusCode"] == 400
    assert body(response)["error"]["code"] == "INVALID_JSON"


def test_post_chat_invalid_payload_returns_400_invalid_request() -> None:
    response = route_request(
        make_api_event("POST", "/chat", body={"message": ""}),
        request_id="req-1",
    )

    assert response["statusCode"] == 400
    assert body(response)["error"]["code"] == "INVALID_REQUEST"


def test_known_path_with_wrong_method_returns_405() -> None:
    response = route_request(make_api_event("GET", "/chat"), request_id="req-1")

    payload = body(response)
    assert response["statusCode"] == 405
    assert payload["error"]["code"] == "METHOD_NOT_ALLOWED"


def test_unknown_path_returns_404() -> None:
    response = route_request(make_api_event("GET", "/missing"), request_id="req-1")

    payload = body(response)
    assert response["statusCode"] == 404
    assert payload["error"]["code"] == "ROUTE_NOT_FOUND"


def test_request_id_is_included_in_controlled_error_response() -> None:
    response = route_request(make_api_event("DELETE", "/health"), request_id="req-123")

    assert body(response)["request_id"] == "req-123"
