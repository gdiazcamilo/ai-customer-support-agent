# src/tools/knowledge.py

from services.knowledge_base import retrieve_knowledge

# TEMPORARY: Set to False (or remove this block) to resume Bedrock Knowledge Base
# retrieval after manual testing.
USE_MOCK_POLICY_SEARCH = True

MOCK_POLICY_SEARCH_RESULT = {
    "results": [
        {
            "text": (
                "Standard shipping normally takes 5 to 7 business days. "
                "Orders can be returned within 30 days of delivery when they are "
                "unused and in their original packaging."
            ),
            "score": 0.99,
            "source": "s3://mock-knowledge-base/policies/shipping-and-returns.md",
        }
    ]
}


def search_policies(query: str, *, request_id: str | None = None) -> dict:
    if USE_MOCK_POLICY_SEARCH:
        return MOCK_POLICY_SEARCH_RESULT

    results = retrieve_knowledge(
        query=query,
        number_of_results=1,
        request_id=request_id,
    )

    return {
        "results": results,
    }
