from __future__ import annotations

import json
from pathlib import Path

from src.llm_factory import LLMClient

_EXTRACT_ENTITIES_PROMPT = (
    Path(__file__).parent / "prompts" / "extract_entities_system.md"
).read_text(encoding="utf-8")


def extract_entities(
    document: dict,
    search_fields: list[str],
    client: LLMClient,
    model: str = "gpt-4o-mini",
) -> list[str]:
    """Extract named entities from the *search_fields* of *document* using an LLM.

    Parameters
    ----------
    document:
        JSON object containing metadata fields and search fields.
    search_fields:
        Keys whose values will be used for entity extraction.
        Fields not present in *document* are silently ignored.

    Returns a list of entity name strings found in the search fields.
    """
    search_text = "\n".join(
        str(document[field])
        for field in search_fields
        if field in document
    )
    if not search_text.strip():
        return []
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": _EXTRACT_ENTITIES_PROMPT},
            {"role": "user", "content": search_text},
        ],
        response_format={"type": "json_object"},
        temperature=0.0,
    )
    raw = response.choices[0].message.content or "{}"
    return json.loads(raw).get("entities", [])



def entity_document_search(
    entities: list[str],
    corpus: list[str],
) -> dict[str, list[str]]:
    """Return all corpus documents that mention each entity.

    Parameters
    ----------
    entities:
        List of entity name strings to look up.
    corpus:
        The collection of documents to search through.

    Returns
    -------
    dict[str, list[str]]
        Mapping of entity name → documents from *corpus* that contain the entity
        (case-insensitive substring match).
    """
    return {
        entity: [doc for doc in corpus if entity.lower() in doc.lower()]
        for entity in entities
    }
