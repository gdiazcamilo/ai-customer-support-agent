import pytest

from tools.erros import InvalidToolInputError
from tools.registry import SEARCH_POLICIES


def test_search_policies_validator_requires_query():
    query = "How long does shipping take?"

    assert SEARCH_POLICIES.validator({"query": query}) == {"query": query}

    with pytest.raises(
        InvalidToolInputError,
        match="query must be a non-empty string",
    ):
        SEARCH_POLICIES.validator({"order_id": "ORD-123"})
