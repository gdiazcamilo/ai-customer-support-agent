import json
import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from aws_lambda_typing import context as lambda_context

logger = logging.getLogger()
logger.setLevel("INFO")


def lambda_handler(event: dict[str, any], context: lambda_context.Context):
    logger.info("Salute lambda function invoked. RequestID=%s Event=%s",
                context.aws_request_id, 
                json.dumps(event))

    name = event.get("name", "world");

    return {
        "statusCode": 200,
        "body": {
            "message": f"Hello {name}",
            "request_id": context.aws_request_id
        }

    }