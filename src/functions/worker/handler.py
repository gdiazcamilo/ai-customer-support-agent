from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING, Any

from ..api.logging_utils import log_event

if TYPE_CHECKING:
    from aws_lambda_typing.events import SQSEvent
    from aws_lambda_typing.events.sqs import SQSMessage
from ..api.config import SETTINGS

logger = logging.getLogger()
logger.setLevel(SETTINGS.log_level)


def handler(event: SQSEvent, context: Any) -> dict:
    records = event.get("Records", [])
    failures = []

    log_event(
        logger,
        logging.INFO,
        "support_jobs_batch_started",
        batch_size=len(records),
        lambda_request_id=context.aws_request_id,
    )

    for record in records:
        message_id = record["messageId"]

        try:
            process_record(record)
        except Exception:
            log_event(
                logger, logging.ERROR, "support_job_failed", message_id=message_id
            )

            failures.append({"itemIdentifier": message_id})

    return {"batchItemFailures": failures}


def process_record(record: SQSMessage) -> None:
    message_id = record["messageId"]
    job = json.loads(record["body"])

    receive_count = record.get("attributes", {}).get("ApproximateReceiveCount")

    log_event(
        logger,
        logging.INFO,
        "support_job_received",
        message_id=message_id,
        request_id=job.get("request_id"),
        job_type=job.get("job_type"),
        schema_version=job.get("schema_version"),
        receive_count=receive_count,
    )

    process_job(job)

    log_event(
        logger,
        logging.INFO,
        "support_job_completed",
        message_id=message_id,
        request_id=job.get("request_id"),
    )


def process_job(job: dict[str, Any]) -> None:
    # Por ahora simulamos el procesamiento.
    message = job["message"]

    log_event(
        logger,
        logging.INFO,
        "support_message_processed",
        request_id=job.get("request_id"),
        message_length=len(message),
    )
