from __future__ import annotations

import hashlib
import json
from typing import Any

# Learning-only in-memory idempotency store.
# Not suitable for Lambda production workloads.
PROCESSED_ACTIONS: dict[str, Any] = {}


def build_idempotency_key(
    tool_name: str,
    arguments: dict[str, Any],
) -> str:
    payload = {
        "tool_name": tool_name,
        "arguments": arguments,
    }

    canonical_payload = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
    )

    return hashlib.sha256(canonical_payload.encode("utf-8")).hexdigest()


def get_processed_result(key: str) -> Any | None:
    return PROCESSED_ACTIONS.get(key)


def save_processed_result(
    key: str,
    result: Any,
) -> None:
    PROCESSED_ACTIONS[key] = result
