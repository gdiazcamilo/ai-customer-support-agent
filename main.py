import logging

from local_environment import configure_local_environment

configure_local_environment()

from agentcore_config import AGENTCORE_SETTINGS

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
    "What's the return policy?"
]

for question in QUESTIONS:
    print()
    print("=" * 80)
    print("QUESTION:", question)

    result = run_agent(question, request_id="test-request-id")

    print("ANSWER:", result.answer)
    print("SOURCES:", result.retrieved_sources)
