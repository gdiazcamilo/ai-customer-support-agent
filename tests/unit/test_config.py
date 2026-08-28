import pytest

from agentcore_config import load_agentcore_settings
from functions.api.config import load_api_settings
from functions.worker.config import load_worker_settings


def test_api_settings_require_only_the_queue_url() -> None:
    settings = load_api_settings({"SUPPORT_JOBS_QUEUE_URL": "https://example.com/jobs"})

    assert settings.support_jobs_queue_url == "https://example.com/jobs"
    assert settings.service_name == "ai-customer-support-agent"
    assert settings.environment == "dev"
    assert settings.log_level == "INFO"


def test_worker_settings_require_only_the_agentcore_runtime_arn() -> None:
    settings = load_worker_settings(
        {"AGENTCORE_RUNTIME_ARN": "arn:aws:bedrock-agentcore:runtime/test"}
    )

    assert settings.agentcore_runtime_arn.endswith("runtime/test")
    assert settings.service_name == "ai-customer-support-worker"
    assert settings.environment == "dev"
    assert settings.log_level == "INFO"


def test_agentcore_settings_require_only_its_runtime_dependencies() -> None:
    settings = load_agentcore_settings(
        {
            "BEDROCK_MODEL_ID": "test-model",
            "KNOWLEDGE_BASE_ID": "test-knowledge-base",
            "AGENTCORE_MEMORY_ID": "test-memory",
        }
    )

    assert settings.bedrock_model_id == "test-model"
    assert settings.knowledge_base_id == "test-knowledge-base"
    assert settings.memory_id == "test-memory"
    assert settings.service_name == "ai-customer-support-agentcore"
    assert settings.environment == "dev"
    assert settings.log_level == "INFO"


@pytest.mark.parametrize(
    ("loader", "required_variable"),
    [
        (load_api_settings, "SUPPORT_JOBS_QUEUE_URL"),
        (load_worker_settings, "AGENTCORE_RUNTIME_ARN"),
        (load_agentcore_settings, "BEDROCK_MODEL_ID"),
    ],
)
def test_missing_required_runtime_setting_fails_fast(loader, required_variable) -> None:
    with pytest.raises(KeyError, match=required_variable):
        loader({})
