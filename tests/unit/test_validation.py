import base64

import pytest

from src.functions.api.validation import (
    MAX_MESSAGE_LENGTH,
    ValidationError,
    parse_json_body,
    validate_chat_payload,
)

from .event_factory import make_api_event


def assert_validation_error(
    exc_info: pytest.ExceptionInfo[ValidationError],
    code: str,
    message_fragment: str,
) -> None:
    assert exc_info.value.code == code
    assert message_fragment in exc_info.value.message


def test_parse_json_body_valid_json_object_is_parsed() -> None:
    assert parse_json_body(make_api_event(body={"message": "hello"})) == {
        "message": "hello",
    }


def test_parse_json_body_base64_encoded_json_is_decoded_and_parsed() -> None:
    body = base64.b64encode(b'{"message": "hello"}').decode("ascii")

    assert parse_json_body(make_api_event(body=body, is_base64_encoded=True)) == {
        "message": "hello",
    }


@pytest.mark.parametrize("body", [None, ""])
def test_parse_json_body_missing_or_empty_body_is_rejected(
    body: str | None,
) -> None:
    with pytest.raises(ValidationError) as exc_info:
        parse_json_body(make_api_event(body=body))

    assert_validation_error(exc_info, "INVALID_JSON", "valid JSON")


@pytest.mark.parametrize("body", ["{", "plain text"])
def test_parse_json_body_invalid_json_text_is_rejected(body: str) -> None:
    with pytest.raises(ValidationError) as exc_info:
        parse_json_body(make_api_event(body=body))

    assert_validation_error(exc_info, "INVALID_JSON", "valid JSON")


@pytest.mark.parametrize("body", ["[]", '"hello"', "123", "null"])
def test_parse_json_body_non_object_json_values_are_rejected(body: str) -> None:
    with pytest.raises(ValidationError) as exc_info:
        parse_json_body(make_api_event(body=body))

    assert_validation_error(exc_info, "INVALID_REQUEST", "JSON object")


def test_validate_chat_payload_trims_surrounding_whitespace() -> None:
    assert validate_chat_payload({"message": "  hello  "}) == "hello"


def test_validate_chat_payload_missing_message_is_rejected() -> None:
    with pytest.raises(ValidationError) as exc_info:
        validate_chat_payload({})

    assert_validation_error(exc_info, "INVALID_REQUEST", "required")


def test_validate_chat_payload_non_string_message_is_rejected() -> None:
    with pytest.raises(ValidationError) as exc_info:
        validate_chat_payload({"message": 123})

    assert_validation_error(exc_info, "INVALID_REQUEST", "must be a string")


@pytest.mark.parametrize("message", ["", "   "])
def test_validate_chat_payload_empty_message_is_rejected(message: str) -> None:
    with pytest.raises(ValidationError) as exc_info:
        validate_chat_payload({"message": message})

    assert_validation_error(exc_info, "INVALID_REQUEST", "must not be empty")


def test_validate_chat_payload_message_longer_than_limit_is_rejected() -> None:
    with pytest.raises(ValidationError) as exc_info:
        validate_chat_payload({"message": "a" * (MAX_MESSAGE_LENGTH + 1)})

    assert_validation_error(exc_info, "INVALID_REQUEST", str(MAX_MESSAGE_LENGTH))


def test_validate_chat_payload_message_at_limit_is_accepted() -> None:
    message = "a" * MAX_MESSAGE_LENGTH

    assert validate_chat_payload({"message": message}) == message


def test_validate_chat_payload_unknown_fields_are_rejected() -> None:
    with pytest.raises(ValidationError) as exc_info:
        validate_chat_payload({"message": "hello", "extra": True})

    assert_validation_error(exc_info, "INVALID_REQUEST", "unsupported fields")
