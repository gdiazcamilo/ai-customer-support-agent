import os
from collections.abc import Mapping
from dataclasses import dataclass


@dataclass(frozen=True)
class WorkerSettings:
    service_name: str
    environment: str
    log_level: str
    agentcore_runtime_arn: str


def load_worker_settings(
    environ: Mapping[str, str] | None = None,
) -> WorkerSettings:
    values = os.environ if environ is None else environ

    return WorkerSettings(
        service_name=values.get(
            "SERVICE_NAME",
            "ai-customer-support-worker",
        ),
        environment=values.get("APP_ENV", "dev"),
        log_level=values.get("LOG_LEVEL", "INFO"),
        agentcore_runtime_arn=values["AGENTCORE_RUNTIME_ARN"],
    )


WORKER_SETTINGS = load_worker_settings()
