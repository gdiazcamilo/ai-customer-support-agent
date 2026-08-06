import json
import logging
from types import SimpleNamespace

logging.basicConfig(level=logging.INFO, format="%(message)s")

from src.functions.api.handler import handler

event = {
    "version": "2.0",
    "rawPath": "/health",
    "requestContext": {
        "requestId": "local-api-request-123",
        "http": {
            "method": "GET",
            "path": "/health",
        },
    },
}

context = SimpleNamespace(
    aws_request_id="local-lambda-request-456",
)

response = handler(event, context)

print(json.dumps(response, indent=2))