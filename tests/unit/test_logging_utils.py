import logging
from unittest.mock import Mock

from functions.api.logging_utils import log_event


def test_log_event_prints_to_console_when_running_locally(
    capsys,
    monkeypatch,
) -> None:
    monkeypatch.delenv("AWS_EXECUTION_ENV", raising=False)
    monkeypatch.delenv("AWS_LAMBDA_FUNCTION_NAME", raising=False)
    logger = Mock(spec=logging.Logger)

    log_event(
        logger=logger,
        level=logging.INFO,
        event_name="request_started",
        request_id="request-1",
    )

    assert capsys.readouterr().out == (
        '{"event": "request_started", "request_id": "request-1"}\n'
    )


def test_log_event_does_not_print_to_console_when_running_in_lambda(
    capsys,
    monkeypatch,
) -> None:
    monkeypatch.setenv("AWS_EXECUTION_ENV", "AWS_Lambda_python3.14")
    logger = Mock(spec=logging.Logger)

    log_event(
        logger=logger,
        level=logging.INFO,
        event_name="request_started",
        request_id="request-1",
    )

    assert capsys.readouterr().out == ""
    logger.log.assert_called_once()
