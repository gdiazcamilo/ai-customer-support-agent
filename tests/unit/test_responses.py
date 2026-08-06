import json

from src.functions.api.responses import error_response, json_response, success_response


def response_body(response: dict[str, object]) -> dict[str, object]:
    return json.loads(response["body"])  # type: ignore[arg-type]


def test_json_response_uses_requested_status_code() -> None:
    response = json_response(201, {"ok": True})

    assert response["statusCode"] == 201


def test_json_response_serializes_body_as_json_string() -> None:
    response = json_response(200, {"ok": True})

    assert isinstance(response["body"], str)
    assert response_body(response) == {"ok": True}


def test_json_response_sets_json_content_type() -> None:
    response = json_response(200, {"ok": True})

    assert response["headers"]["content-type"] == "application/json"


def test_success_response_uses_data_envelope() -> None:
    response = success_response({"message": "hello"}, request_id="req-1")

    assert response_body(response) == {
        "data": {"message": "hello"},
        "request_id": "req-1",
    }


def test_success_response_supports_custom_status_code() -> None:
    response = success_response({}, request_id="req-1", status_code=202)

    assert response["statusCode"] == 202


def test_error_response_uses_error_envelope() -> None:
    response = error_response(400, "BAD", "Bad request", request_id="req-1")

    assert response_body(response) == {
        "error": {
            "code": "BAD",
            "message": "Bad request",
        },
        "request_id": "req-1",
    }


def test_response_headers_are_not_shared_between_responses() -> None:
    first = json_response(200, {"ok": True})
    second = json_response(200, {"ok": True})

    first["headers"]["x-test"] = "mutated"

    assert "x-test" not in second["headers"]
