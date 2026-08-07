import logging
from dataclasses import dataclass
from typing import Any

import boto3

from .config import SETTINGS
from .logging_utils import log_event
from .responses import error_response
from .router import route_request

logger = logging.getLogger()
logger.setLevel(SETTINGS.log_level)


@dataclass(frozen=True)
class RequestIdentifier:
    value: str
    source: str




sqs = boto3.client("sqs")

def handler(
    event: dict[str, Any],
    context: Any,
) -> dict[str, Any]:
    request_identifier = extract_request_id(
        event=event,
        context=context,
    )
    lambda_request_id = extract_lambda_request_id(context)

    method = (
        event.get("requestContext", {})
        .get("http", {})
        .get("method")
    )
    path = event.get("rawPath")

    log_event(
        logger=logger,
        level=logging.INFO,
        event_name="request_started",
        request_id=request_identifier.value,
        request_id_source=request_identifier.source,
        lambda_request_id=lambda_request_id,
        method=method,
        path=path,
    )

    try:
        response = route_request(
            event=event,
            request_id=request_identifier.value,
        )
    except Exception:
        log_event(
            logger=logger,
            level=logging.ERROR,
            event_name="request_failed",
            request_id=request_identifier.value,
            request_id_source=request_identifier.source,
            lambda_request_id=lambda_request_id,
            method=method,
            path=path,
        )

        logger.exception(
            "Unexpected error while processing request"
        )

        return error_response(
            status_code=500,
            code="INTERNAL_ERROR",
            message="An unexpected error occurred.",
            request_id=request_identifier.value,
        )

    log_event(
        logger=logger,
        level=logging.INFO,
        event_name="request_completed",
        request_id=request_identifier.value,
        request_id_source=request_identifier.source,
        lambda_request_id=lambda_request_id,
        method=method,
        path=path,
        status_code=response["statusCode"],
    )

    return response


def extract_request_id(
    event: dict[str, Any],
    context: Any,
) -> RequestIdentifier:
    api_gateway_request_id = (
        event.get("requestContext", {})
        .get("requestId")
    )

    if api_gateway_request_id:
        return RequestIdentifier(
            value=api_gateway_request_id,
            source="api_gateway",
        )

    lambda_request_id = getattr(
        context,
        "aws_request_id",
        None,
    )

    if lambda_request_id:
        return RequestIdentifier(
            value=lambda_request_id,
            source="lambda",
        )

    return RequestIdentifier(
        value="unknown",
        source="unknown",
    )


def extract_lambda_request_id(context: Any) -> str:
    return (
        getattr(context, "aws_request_id", None)
        or "unknown"
    )