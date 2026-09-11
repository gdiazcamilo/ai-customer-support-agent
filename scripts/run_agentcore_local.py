#!/usr/bin/env python3
"""Start the AgentCore application locally on http://127.0.0.1:8080.

Example request:
    curl --request POST http://127.0.0.1:8080/invocations \
      --header 'Content-Type: application/json' \
      --data '{"prompt":"What is the status of order ORD-123?","request_id":"local-test"}'
"""

from local_environment import configure_local_environment

configure_local_environment()

# Import only after setting the required AgentCore environment variables.
from agentcore_app import app

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8080)
