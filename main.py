import logging
import os

from agentcore_config import AGENTCORE_SETTINGS

os.environ.setdefault(
    "BEDROCK_MODEL_ID",
    "amazon.nova-micro-v1:0",
)
os.environ["AGENTCORE_MEMORY_ID"] = "ai_customer_support_memory_cdk_dev-9HnRaPFvaB"
os.environ["KNOWLEDGE_BASE_ID"] = "test"

logging.basicConfig(
    level=AGENTCORE_SETTINGS.log_level,
    format="%(message)s",
)

from services.agent import run_agent

QUESTIONS = [
    # "How long do I have to return an unused product?",
    # "Can I return an opened laptop?",
    # "How long does express shipping take?",
    # "Do you ship internationally?",
    # "How long is the warranty on a rechargeable battery?",
    # "Does the warranty cover accidental damage?",
    # "Do you ship to Brazil?",
    # "Do you offer price matching?",
    "Whats the status of order ORD-123?"
]

for question in QUESTIONS:
    print()
    print("=" * 80)
    print("QUESTION:", question)

    result = run_agent(question, request_id="test-request-id")

    print("ANSWER:", result.answer)
    print("SOURCES:", result.retrieved_sources)
