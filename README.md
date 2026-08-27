# AI Customer Support Agent

Python customer support agent built around AWS Lambda, API Gateway, SQS, Amazon Bedrock, and Bedrock AgentCore Runtime.

The HTTP API accepts support chat messages, validates them, and enqueues work for asynchronous processing. The worker invokes the AgentCore runtime, which runs a Bedrock-powered support assistant with local tools for order lookup, customer lookup, order cancellation, and policy search.

## Repository Layout

```text
.
├── docs/                         API contract notes
├── infrastructure/               CloudFormation templates
├── scripts/                      Packaging, smoke test, and local agent scripts
├── src/
│   ├── agentcore_app.py          Bedrock AgentCore Runtime entrypoint
│   ├── functions/
│   │   ├── api/                  API Gateway Lambda handler
│   │   ├── gateway_tools/        AgentCore gateway tool handler
│   │   ├── health/               Health function handler
│   │   ├── salute/               Example function handler
│   │   └── worker/               SQS worker handler
│   ├── services/                 Agent, AgentCore, memory, and knowledge services
│   └── tools/                    Agent tool registry and implementations
└── tests/                        Unit tests
```

## Runtime Flow

1. `POST /chat` receives a JSON body with a support message.
2. The API handler validates the payload and sends a `support_message` job to SQS.
3. The SQS worker reads the job and calls Bedrock AgentCore Runtime.
4. `src/agentcore_app.py` runs the support agent.
5. The agent uses Bedrock Converse and the registered tools when it needs order, customer, or policy data.

`GET /health` is synchronous and returns basic service health.

## API

### `GET /health`

Returns:

```json
{
  "status": "ok",
  "service": "ai-customer-support-agent",
  "environment": "dev"
}
```

### `POST /chat`

Request:

```json
{
  "message": "How long do I have to return an unused product?"
}
```

Successful response:

```json
{
  "data": {
    "status": "accepted",
    "job_id": "sqs-message-id",
    "request_id": "api-request-id"
  },
  "request_id": "api-request-id"
}
```

Validation and error response details are documented in `docs/api-contract.md`.

## Configuration

The application reads configuration from environment variables at import time.

Required:

| Variable | Description |
| --- | --- |
| `SUPPORT_JOBS_QUEUE_URL` | SQS queue URL for support jobs |
| `BEDROCK_MODEL_ID` | Bedrock model ID used by the local Converse agent |
| `KNOWLEDGE_BASE_ID` | Bedrock knowledge base ID used for policy search |
| `AGENTCORE_MEMORY_ID` | AgentCore memory ID for conversation history |

Optional:

| Variable | Default | Description |
| --- | --- | --- |
| `SERVICE_NAME` | `ai-customer-support-agent` | Service name returned by health checks and logs |
| `APP_ENV` | `dev` | Runtime environment name |
| `LOG_LEVEL` | `INFO` | Python logging level |
| `AGENTCORE_RUNTIME_ARN` | unset | Required by the worker when invoking AgentCore Runtime |

`src/agentcore_app.py` sets local-development defaults for the required variables before loading settings.

## Local Setup

Create and activate a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt -r requirements-dev.txt
```

Run tests:

```bash
pytest
```

Run linting/format checks:

```bash
ruff check .
black --check .
```

## AWS CDK

Install the CDK app dependencies:

```bash
npm --prefix infrastructure/cdk install
```

Run CDK commands from the repository root:

```bash
cdk synth
cdk diff
cdk deploy
cdk watch
```

`cdk watch` monitors the application code in `src/`, the CDK app in
`infrastructure/cdk/bin/` and `infrastructure/cdk/lib/`, and
`requirements.txt`.

## Local Agent Scripts

Run a direct agent question:

```bash
PYTHONPATH=src:. python main.py
```

Run the cancellation flow example:

```bash
PYTHONPATH=src:. python scripts/run_agent.py
```

Inspect a Bedrock tool-use round trip:

```bash
PYTHONPATH=src:. python scripts/inspect_tool_use.py
```

These scripts require AWS credentials and access to the configured Bedrock resources.

## Packaging AgentCore Runtime

Build the AgentCore runtime artifact:

```bash
scripts/package_agentcore.sh
```

The script installs production dependencies for `aarch64-manylinux2014` Python 3.14 into `.build/agentcore/`, copies `src/`, and writes `.build/agentcore-runtime.zip`.

## Smoke Test

After deploying the CloudFormation stack, run:

```bash
STACK_NAME=ai-customer-support-agent-dev AWS_PROFILE=admin scripts/smoke-test.sh
```

The script reads `ApiUrl` from the stack outputs and exercises `GET /health` and `POST /chat`.

## Tooling

The agent registers these tools in `src/tools/registry.py`:

| Tool | Purpose |
| --- | --- |
| `get_order` | Retrieve details for a specific order ID |
| `get_customer` | Retrieve details for a specific customer ID |
| `cancel_order` | Cancel a specific order after confirmation |
| `search_policies` | Search company policies and support documentation |

Tool execution is routed through `src/tools/executor.py`, which validates input, handles expected tool errors, and enforces confirmation for side-effecting tools.
