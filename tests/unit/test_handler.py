import json
from types import SimpleNamespace
from unittest.mock import patch

from functions.api.handler import handler
from tests.unit.event_factory import make_api_event


def lambda_context(aws_request_id: str = "lambda-request-id") -> SimpleNamespace:
    return SimpleNamespace(aws_request_id=aws_request_id)


def body(response: dict[str, object]) -> dict[str, object]:
    return json.loads(response["body"])  # type: ignore[arg-type]


def test_valid_health_request_returns_200() -> None:
    response = handler(make_api_event("GET", "/health"), lambda_context())

    assert response["statusCode"] == 200


def test_api_gateway_request_id_is_preferred_when_present() -> None:
    response = handler(
        make_api_event("POST", "/chat", body={"message": "hello"}, request_id="api-1"),
        lambda_context("lambda-1"),
    )

    assert body(response)["request_id"] == "api-1"


def test_lambda_request_id_is_fallback_when_api_gateway_request_id_absent() -> None:
    event = make_api_event("POST", "/chat", body={"message": "hello"}, request_id="")

    response = handler(event, lambda_context("lambda-1"))

    assert body(response)["request_id"] == "lambda-1"


def test_unexpected_route_exception_is_converted_to_500_response() -> None:
    with patch(
        "functions.api.handler.route_request",
        side_effect=RuntimeError("database password leaked"),
    ):
        response = handler(
            make_api_event("GET", "/health", request_id="api-1"),
            lambda_context("lambda-1"),
        )

    assert response["statusCode"] == 500
    assert body(response)["error"]["code"] == "INTERNAL_ERROR"


def test_500_response_does_not_expose_original_exception_message() -> None:
    with patch(
        "functions.api.handler.route_request",
        side_effect=RuntimeError("secret original exception"),
    ):
        response = handler(
            make_api_event("GET", "/health", request_id="api-1"),
            lambda_context("lambda-1"),
        )

    payload = body(response)
    assert payload["error"]["message"] == "An unexpected error occurred."
    assert "secret original exception" not in response["body"]


def test_expected_request_id_is_included_in_500_response() -> None:
    with patch(
        "functions.api.handler.route_request",
        side_effect=RuntimeError("boom"),
    ):
        response = handler(
            make_api_event("GET", "/health", request_id="api-1"),
            lambda_context("lambda-1"),
        )

    assert body(response)["request_id"] == "api-1"


def test_success_logging_paths_do_not_break_execution() -> None:
    with patch("functions.api.handler.log_event") as log_event:
        response = handler(
            make_api_event("GET", "/health", request_id="api-1"),
            lambda_context("lambda-1"),
        )

    assert response["statusCode"] == 200
    assert [call.kwargs["event_name"] for call in log_event.call_args_list] == [
        "request_started",
        "request_completed",
    ]


def test_failure_logging_path_does_not_break_exception_handling() -> None:
    with (
        patch(
            "functions.api.handler.route_request",
            side_effect=RuntimeError("boom"),
        ),
        patch("functions.api.handler.log_event") as log_event,
    ):
        response = handler(
            make_api_event("GET", "/health", request_id="api-1"),
            lambda_context("lambda-1"),
        )

    assert response["statusCode"] == 500
    assert "request_failed" in [
        call.kwargs["event_name"] for call in log_event.call_args_list
    ]
