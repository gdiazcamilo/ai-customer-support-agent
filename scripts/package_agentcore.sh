#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BUILD_DIR="$ROOT_DIR/.build/agentcore"
ZIP_PATH="$ROOT_DIR/.build/agentcore-runtime.zip"

rm -rf "$BUILD_DIR"
rm -f "$ZIP_PATH"

mkdir -p "$BUILD_DIR"

uv pip install \
  --python-platform aarch64-manylinux2014 \
  --python-version 3.14 \
  --target "$BUILD_DIR" \
  --only-binary=:all: \
  -r "$ROOT_DIR/requirements.txt"

cp -R "$ROOT_DIR/src/"* "$BUILD_DIR/"

(
  cd "$BUILD_DIR"
  zip -qr "$ZIP_PATH" .
)

echo "Created: $ZIP_PATH"