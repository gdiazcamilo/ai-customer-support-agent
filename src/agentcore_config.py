import os
from collections.abc import Mapping
from dataclasses import dataclass


@dataclass(frozen=True)
class AgentCoreSettings:
    service_name: str
    environment: str
    log_level: str
    bedrock_model_id: str
    knowledge_base_id: str
    memory_id: str


def load_agentcore_settings(
    environ: Mapping[str, str] | None = None,
) -> AgentCoreSettings:
    values = os.environ if environ is None else environ

    return AgentCoreSettings(
        service_name=values.get(
            "SERVICE_NAME",
            "ai-customer-support-agentcore",
        ),
        environment=values.get("APP_ENV", "dev"),
        log_level=values.get("LOG_LEVEL", "INFO"),
        bedrock_model_id=values["BEDROCK_MODEL_ID"],
        knowledge_base_id=values["KNOWLEDGE_BASE_ID"],
        memory_id=values["AGENTCORE_MEMORY_ID"],
    )


AGENTCORE_SETTINGS = load_agentcore_settings()
