from __future__ import annotations

import logging

import boto3

from functions.api.config import SETTINGS
from functions.api.logging_utils import log_event

logger = logging.getLogger()
logger.setLevel(SETTINGS.log_level)


bedrock_runtime = boto3.client("bedrock-runtime")


SYSTEM_PROMPT = """
You are a concise customer support assistant.

- Answer clearly and briefly.
- Do not invent information.
- If you do not know the answer, say so.
- Do not claim to have performed actions that were not actually performed.
"""


def generate_response(message: str, request_id: str | None) -> str:
    log_event(
        logger,
        logging.INFO,
        "bedrock_inference_started",
        request_id=request_id,
        model_id=SETTINGS.bedrock_model_id,
    )

    response = bedrock_runtime.converse(
        modelId=SETTINGS.bedrock_model_id,
        system=[{"text": SYSTEM_PROMPT}],
        messages=[
            {
                "role": "user",
                "content": [{"text": message}],
            }
        ],
        inferenceConfig={
            "maxTokens": 200,
            "temperature": 0.2,
        },
    )

    usage = response["usage"]
    metrics = response["metrics"]

    log_event(
        logger,
        logging.INFO,
        "bedrock_inference_completed",
        request_id=request_id,
        model_id=SETTINGS.bedrock_model_id,
        input_tokens=usage["inputTokens"],
        output_tokens=usage["outputTokens"],
        total_tokens=usage["totalTokens"],
        latency_ms=metrics["latencyMs"],
        stop_reason=response["stopReason"],
    )

    return response["output"]["message"]["content"][0]["text"]
