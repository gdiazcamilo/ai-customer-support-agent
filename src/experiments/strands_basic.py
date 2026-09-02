from strands import Agent
from strands.models import BedrockModel

from services.memory import load_conversation
from tools.strands_adapters import STRANDS_TOOLS, build_request_state

history = load_conversation(
    actor_id="support-user", conversation_id="test-conversation-1"
)

model = BedrockModel(
    model_id="amazon.nova-micro-v1:0",
    temperature=0,
)

agent = Agent(
    model=model,
    tools=STRANDS_TOOLS,
    system_prompt=(
        """You are a customer support assistant.
For company policy questions, use the search_policies tool.
Answer policy questions only using information returned by that tool.
If the tool does not provide enough information, say you do not have enough information.
"""
    ),
    # messages=[Message(**m) for m in history],
    callback_handler=None,
)

request_state = build_request_state(
    request_id="req-123",
)

result = agent(
    "What's the status of my order ORD-123?",
    invocation_state={
        "request_state": request_state,
    },
)

print("ANSWER:")
print(result)

print("RESULT STATE:")
print(result.state)

print("SOURCES:")
print(result.state["retrieved_sources"])
