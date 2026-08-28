#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TEMPLATE_FILE="$ROOT_DIR/infrastructure/template.yaml"
PACKAGED_TEMPLATE_FILE="$ROOT_DIR/.build/cloudformation/packaged-template.yaml"

AWS_PROFILE="${AWS_PROFILE:-}"
AWS_REGION="${AWS_REGION:-}"

if [[ -z "${ENVIRONMENT_NAME:-}" ]]; then
  read -r -p "Environment name [dev]: " ENVIRONMENT_NAME
  ENVIRONMENT_NAME="${ENVIRONMENT_NAME:-dev}"
fi

if [[ "$ENVIRONMENT_NAME" != "dev" && "$ENVIRONMENT_NAME" != "prod" ]]; then
  echo "ENVIRONMENT_NAME must be either dev or prod."
  exit 1
fi

if [[ -z "${STACK_NAME:-}" ]]; then
  DEFAULT_STACK_NAME="ai-customer-support-agent-$ENVIRONMENT_NAME"
  read -r -p "CloudFormation stack name [$DEFAULT_STACK_NAME]: " STACK_NAME
  STACK_NAME="${STACK_NAME:-$DEFAULT_STACK_NAME}"
fi

if [[ -z "${ARTIFACT_BUCKET:-}" ]]; then
  DEFAULT_ARTIFACT_BUCKET="squad-prep-artifacts-214078205303-us-east-1"
  read -r -p "Existing S3 artifact bucket [$DEFAULT_ARTIFACT_BUCKET]: " ARTIFACT_BUCKET
  ARTIFACT_BUCKET="${ARTIFACT_BUCKET:-$DEFAULT_ARTIFACT_BUCKET}"
fi

if [[ -z "${S3_PREFIX:-}" ]]; then
  DEFAULT_S3_PREFIX="ai-customer-support-agent/$ENVIRONMENT_NAME"
  read -r -p "S3 artifact prefix [$DEFAULT_S3_PREFIX]: " S3_PREFIX
  S3_PREFIX="${S3_PREFIX:-$DEFAULT_S3_PREFIX}"
fi

if ! command -v aws >/dev/null 2>&1; then
  echo "The AWS CLI is required but was not found in PATH."
  exit 1
fi

mkdir -p "$(dirname "$PACKAGED_TEMPLATE_FILE")"

AWS_ARGS=()

if [[ -n "$AWS_PROFILE" ]]; then
  AWS_ARGS+=(--profile "$AWS_PROFILE")
fi

if [[ -n "$AWS_REGION" ]]; then
  AWS_ARGS+=(--region "$AWS_REGION")
fi

run_aws() {
  if [[ "${#AWS_ARGS[@]}" -gt 0 ]]; then
    aws "$@" "${AWS_ARGS[@]}"
  else
    aws "$@"
  fi
}

echo "Packaging local Lambda code into s3://$ARTIFACT_BUCKET/$S3_PREFIX ..."
run_aws cloudformation package \
  --template-file "$TEMPLATE_FILE" \
  --s3-bucket "$ARTIFACT_BUCKET" \
  --s3-prefix "$S3_PREFIX" \
  --output-template-file "$PACKAGED_TEMPLATE_FILE"

echo "Deploying CloudFormation stack $STACK_NAME ..."
run_aws cloudformation deploy \
  --template-file "$PACKAGED_TEMPLATE_FILE" \
  --stack-name "$STACK_NAME" \
  --parameter-overrides "EnvironmentName=$ENVIRONMENT_NAME" \
  --capabilities CAPABILITY_IAM \
  --no-fail-on-empty-changeset

echo "Stack outputs:"
run_aws cloudformation describe-stacks \
  --stack-name "$STACK_NAME" \
  --query 'Stacks[0].Outputs[*].[OutputKey,OutputValue]' \
  --output table
