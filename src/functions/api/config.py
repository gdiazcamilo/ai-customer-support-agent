import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    service_name: str
    environment: str
    log_level: str
    support_jobs_queue_url: str


def load_settings() -> Settings:
    return Settings(
        service_name=os.environ.get(
            "SERVICE_NAME",
            "ai-customer-support-agent",
        ),
        environment=os.environ.get(
            "APP_ENV",
            "dev",
        ),
        log_level=os.environ.get(
            "LOG_LEVEL",
            "INFO",
        ),
        support_jobs_queue_url=os.environ["SUPPORT_JOBS_QUEUE_URL"]
    )

SETTINGS = load_settings()