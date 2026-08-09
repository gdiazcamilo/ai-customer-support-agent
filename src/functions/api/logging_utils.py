import json
import logging
from typing import Any


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

    print(
        json.dumps(
            payload,
            default=str,
        ),
        flush=True,
    )
