"""Environment configuration for local scripts, experiments, and tests."""

from __future__ import annotations

import os
from collections.abc import Mapping

LOCAL_ENVIRONMENT: Mapping[str, str] = {
    "BEDROCK_MODEL_ID": "amazon.nova-micro-v1:0",
    "AGENTCORE_MEMORY_ID": "ai_customer_support_memory_cdk_dev-9HnRaPFvaB",
    "KNOWLEDGE_BASE_ID": "DIKIIXYIPN",
    "BEDROCK_SYSTEM_PROMPT_PARAMETER_NAME": (
        "/ai-customer-support/dev/bedrock-system-prompt-arn"
    ),
    "SUPPORT_JOBS_QUEUE_URL": "https://example.com/support-jobs",
    "AGENTCORE_RUNTIME_ARN": (
        "arn:aws:bedrock-agentcore:us-east-1:123456789012:runtime/test"
    ),
    "AWS_DEFAULT_REGION": "us-east-1",
    "AWS_EC2_METADATA_DISABLED": "true",
    "BEDROCK_GUARDRAIL_ID": "ozd6ai1dkggd",
    "BEDROCK_GUARDRAIL_VERSION": "3",
}


def configure_local_environment() -> None:
    """Set the environment used by local scripts, experiments, and tests."""
    os.environ.update(LOCAL_ENVIRONMENT)
