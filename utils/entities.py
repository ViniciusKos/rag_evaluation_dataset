from __future__ import annotations

from src.entity_search import extract_entities
from src.llm_factory import LLMClient


def extract_all_entities(
    documents: list[dict],
    search_fields: list[str],
    client: LLMClient,
    model: str,
) -> list[str]:
    """Extract entities from every document and return a deduplicated list."""
    seen: set[str] = set()
    ordered: list[str] = []
    for i, doc in enumerate(documents):
        entities = extract_entities(doc, search_fields, client, model=model)
        print(f"[info] Document {i + 1}/{len(documents)}: {len(entities)} entity(ies) extracted.")
        for entity in entities:
            if entity not in seen:
                seen.add(entity)
                ordered.append(entity)
    print(f"[info] Total unique entities: {len(ordered)}.")
    return ordered
