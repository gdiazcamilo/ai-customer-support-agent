from __future__ import annotations

import json
import os

import boto3

from tools.executor import execute_tool
from tools.orders import OrderNotFoundError
from tools.specs import GET_ORDER_TOOL


MODEL_ID = os.getenv(
    "BEDROCK_MODEL_ID",
    "amazon.nova-micro-v1:0",
)

bedrock_runtime = boto3.client("bedrock-runtime")

messages = [
    {
        "role": "user",
        "content": [{"text": "Where is order ORD-999?"}],
    }
]


# First turn: let the model decide whether it needs a tool.
response = bedrock_runtime.converse(
    modelId=MODEL_ID,
    system=[
        {
            "text": (
                "You are a customer support assistant. "
                "Use the available tools when they are needed "
                "to answer the user's request."
            )
        }
    ],
    messages=messages,
    toolConfig={
        "tools": [
            GET_ORDER_TOOL,
        ]
    },
    inferenceConfig={
        "maxTokens": 200,
        "temperature": 0.2,
    },
)

print("FIRST RESPONSE")
print("stopReason:", response["stopReason"])
print(
    json.dumps(
        response["output"]["message"],
        indent=2,
    )
)


# The assistant message must become part of the conversation history.
assistant_message = response["output"]["message"]
messages.append(assistant_message)


tool_use = next(
    (block["toolUse"] for block in assistant_message["content"] if "toolUse" in block),
    None,
)

if tool_use is None:
    raise RuntimeError("Model did not request a tool")


print("\nTOOL REQUEST")
print(json.dumps(tool_use, indent=2))


# Execute trusted application code.
try:
    tool_result_data = execute_tool(
        tool_use["name"],
        tool_use["input"],
    )

    tool_result = {
        "toolUseId": tool_use["toolUseId"],
        "content": [
            {
                "json": tool_result_data,
            }
        ],
        "status": "success",
    }

except OrderNotFoundError as exc:
    tool_result = {
        "toolUseId": tool_use["toolUseId"],
        "content": [
            {
                "text": str(exc),
            }
        ],
        "status": "error",
    }

print("\nTOOL EXECUTION RESULT")
print(json.dumps(tool_result, indent=2))


# Return the result to the model.
tool_result_message = {
    "role": "user",
    "content": [
        {
            "toolResult": tool_result,
        }
    ],
}

messages.append(tool_result_message)


print("\nMESSAGES SENT TO SECOND CONVERSE CALL")
print(json.dumps(messages, indent=2))


# Second turn: Bedrock now has the real tool result.
final_response = bedrock_runtime.converse(
    modelId=MODEL_ID,
    system=[
        {
            "text": (
                "You are a customer support assistant. "
                "Use the available tools when they are needed "
                "to answer the user's request."
            )
        }
    ],
    messages=messages,
    toolConfig={
        "tools": [
            GET_ORDER_TOOL,
        ]
    },
    inferenceConfig={
        "maxTokens": 200,
        "temperature": 0.2,
    },
)


print("\nFINAL RESPONSE")
print("stopReason:", final_response["stopReason"])
print(
    json.dumps(
        final_response["output"]["message"],
        indent=2,
    )
)
