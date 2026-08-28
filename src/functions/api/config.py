import os
from collections.abc import Mapping
from dataclasses import dataclass


@dataclass(frozen=True)
class ApiSettings:
    service_name: str
    environment: str
    log_level: str
    support_jobs_queue_url: str


def load_api_settings(
    environ: Mapping[str, str] | None = None,
) -> ApiSettings:
    values = os.environ if environ is None else environ

    return ApiSettings(
        service_name=values.get(
            "SERVICE_NAME",
            "ai-customer-support-agent",
        ),
        environment=values.get(
            "APP_ENV",
            "dev",
        ),
        log_level=values.get(
            "LOG_LEVEL",
            "INFO",
        ),
        support_jobs_queue_url=values["SUPPORT_JOBS_QUEUE_URL"],
    )


API_SETTINGS = load_api_settings()
