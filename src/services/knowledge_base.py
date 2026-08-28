from __future__ import annotations

import logging
import time

import boto3

from agentcore_config import AGENTCORE_SETTINGS
from functions.api.logging_utils import log_event

logger = logging.getLogger()
logger.setLevel(AGENTCORE_SETTINGS.log_level)

bedrock_agent_runtime = boto3.client("bedrock-agent-runtime")


def retrieve_knowledge(
    query: str,
    number_of_results: int = 1,
    request_id: str | None = None,
) -> list[dict]:
    log_event(
        logger,
        logging.INFO,
        "knowledge_retrieval_started",
        request_id=request_id,
        knowledge_base_id=AGENTCORE_SETTINGS.knowledge_base_id,
        number_of_results=number_of_results,
        query_length=len(query),
    )

    started_at = time.perf_counter()

    response = bedrock_agent_runtime.retrieve(
        knowledgeBaseId=AGENTCORE_SETTINGS.knowledge_base_id,
        retrievalQuery={
            "text": query,
        },
        retrievalConfiguration={
            "vectorSearchConfiguration": {
                "numberOfResults": number_of_results,
            }
        },
    )

    latency_ms = round((time.perf_counter() - started_at) * 1000)

    results = []

    for item in response.get("retrievalResults", []):
        content = item.get("content", {})
        location = item.get("location", {})
        s3_location = location.get("s3Location", {})

        results.append(
            {
                "text": content.get("text", ""),
                "score": item.get("score"),
                "source": s3_location.get("uri"),
            }
        )

    log_event(
        logger,
        logging.INFO,
        "knowledge_retrieval_completed",
        request_id=request_id,
        knowledge_base_id=AGENTCORE_SETTINGS.knowledge_base_id,
        result_count=len(results),
        top_score=results[0]["score"] if results else None,
        sources=[result["source"] for result in results if result["source"]],
        latency_ms=latency_ms,
    )

    return results
