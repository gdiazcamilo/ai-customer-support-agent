# src/tools/knowledge.py

from services.knowledge_base import retrieve_knowledge


def search_policies(query: str, *, request_id: str | None = None) -> dict:
    results = retrieve_knowledge(
        query=query,
        number_of_results=1,
        request_id=request_id,
    )

    return {
        "results": results,
    }
