import json
import logging
from typing import Any

import boto3

from .config import SETTINGS
from .logging_utils import log_event

STATIC_CHAT_RESPONSE = "The support agent is not connected to AI yet."

logger = logging.getLogger()
logger.setLevel(SETTINGS.log_level)

sqs_client = boto3.client("sqs")

def get_health_status(
    service_name: str,
    environment: str,
) -> dict[str, str]:
    return {
        "status": "ok",
        "service": service_name,
        "environment": environment,
    }


def process_chat(message: str, request_id: str) -> dict:
    job = {
        "schema_version": 1,
        "job_type": "support_message",
        "request_id": request_id,
        "message": message,
    }

    response = sqs_client.send_message(
        QueueUrl=SETTINGS.support_jobs_queue_url,
        MessageBody=json.dumps(job),
    )

    log_event(logger, 
              logging.INFO, 
              event_name="support_job_enqueued",
              event="support_job_enqueued",
              request_id=request_id,
              message_id=response["MessageId"],
              queue="support-jobs")

    return {
        "status": "accepted",
        "job_id": response["MessageId"],
        "request_id": request_id,
    }