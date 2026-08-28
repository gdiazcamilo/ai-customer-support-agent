#!/usr/bin/env bash

set -euo pipefail

STACK_NAME="${STACK_NAME:-ai-customer-support-agent-dev}"
AWS_PROFILE="${AWS_PROFILE:-admin}"

echo "StackName: $STACK_NAME"
API_URL=$(
  aws cloudformation describe-stacks \
    --stack-name "$STACK_NAME" \
    --query "Stacks[0].Outputs[?OutputKey=='ApiUrl'].OutputValue" \
    --output text \
    --profile "$AWS_PROFILE"
)

if [[ -z "$API_URL" || "$API_URL" == "None" ]]; then
  echo "Could not obtain ApiUrl from stack $STACK_NAME."
  exit 1
fi

echo "Testing API: $API_URL"
echo

echo "1. GET /health"
curl --fail-with-body \
  --silent \
  --show-error \
  "$API_URL/health"
echo
echo

echo "2. POST /chat"
curl --fail-with-body \
  --silent \
  --show-error \
  -X POST "$API_URL/chat" \
  -H "Content-Type: application/json" \
  -d '{"message":"Where is my order?"}'
echo
echo

echo "Smoke tests passed."