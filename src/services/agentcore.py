from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass

import boto3

from functions.api.logging_utils import log_event
from functions.worker.config import WORKER_SETTINGS

agentcore_runtime = boto3.client("bedrock-agentcore")

logger = logging.getLogger()
logger.setLevel(WORKER_SETTINGS.log_level)


@dataclass
class AgentCoreResult:
    answer: str
    retrieved_sources: list[str]
    runtime_session_id: str | None = None


def invoke_agent(
    message: str,
    *,
    request_id: str | None = None,
    conversation_id: str | None = None,
) -> AgentCoreResult:
    payload_data = {
        "prompt": message,
        "request_id": request_id,
    }

    if conversation_id is not None:
        payload_data["conversation_id"] = conversation_id

    payload = json.dumps(payload_data).encode("utf-8")

    log_event(
        logger,
        logging.INFO,
        "agentcore_invocation_started",
        request_id=request_id,
    )

    started_at = time.perf_counter()

    response = agentcore_runtime.invoke_agent_runtime(
        agentRuntimeArn=WORKER_SETTINGS.agentcore_runtime_arn,
        qualifier="DEFAULT",
        contentType="application/json",
        accept="application/json",
        payload=payload,
    )

    body = response["response"].read()

    latency_ms = round((time.perf_counter() - started_at) * 1000)
    log_event(
        logger,
        logging.INFO,
        "agentcore_invocation_completed",
        request_id=request_id,
        runtime_session_id=response.get("runtimeSessionId"),
        status_code=response.get("statusCode"),
        latency_ms=latency_ms,
    )

    result = json.loads(body)

    return AgentCoreResult(
        answer=result["answer"],
        retrieved_sources=result.get("retrieved_sources", []),
        runtime_session_id=response.get("runtimeSessionId"),
    )
