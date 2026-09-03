import json
import logging
import os
from typing import Any

AWS_RUNTIME_ENVIRONMENT_VARIABLES = (
    "AWS_EXECUTION_ENV",
    "AWS_LAMBDA_FUNCTION_NAME",
)


def log_event(
    logger: logging.Logger,
    level: int,
    event_name: str,
    **fields: Any,
) -> None:
    payload = {
        "event": event_name,
        **fields,
    }

    logger.log(
        level,
        json.dumps(
            payload,
            default=str,
        ),
    )
