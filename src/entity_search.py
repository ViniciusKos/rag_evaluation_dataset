from __future__ import annotations

import json
from pathlib import Path

from src.embedding_search import find_top_n_similar, get_embeddings
from src.llm_factory import LLMClient

_EXTRACT_ENTITIES_PROMPT = (
    Path(__file__).parent / "prompts" / "extract_entities_system.md"
).read_text(encoding="utf-8")


def extract_entities(
    document: str,
    client: LLMClient,
    model: str = "gpt-4o-mini",
) -> list[str]:
    """Extract named entities from *document* using an LLM.

    Returns a list of entity name strings.
    """
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": _EXTRACT_ENTITIES_PROMPT},
            {"role": "user", "content": document},
        ],
        response_format={"type": "json_object"},
        temperature=0.0,
    )
    raw = response.choices[0].message.content or "{}"
    return json.loads(raw).get("entities", [])


def search_documents_by_entity(
    entity: str,
    corpus: list[str],
    n: int,
    client: LLMClient,
    embedding_model: str = "text-embedding-3-small",
) -> list[str]:
    """Return the *n* documents from *corpus* most semantically similar to *entity*.

    The entity and all corpus texts are embedded in a single API call to
    minimise latency and cost.
    """
    all_embeddings = get_embeddings([entity] + corpus, client, embedding_model)
    query_embedding = all_embeddings[0]
    corpus_embeddings = all_embeddings[1:]
    top_indices = find_top_n_similar(query_embedding, corpus_embeddings, n)
    return [corpus[i] for i in top_indices]


def entity_document_search(
    source_document: str,
    corpus: list[str],
    n: int,
    client: LLMClient,
    chat_model: str = "gpt-4o-mini",
    embedding_model: str = "text-embedding-3-small",
) -> dict[str, list[str]]:
    """Extract entities from *source_document* and retrieve the top-*n* related docs.

    Parameters
    ----------
    source_document:
        The document from which entities are extracted.
    corpus:
        The collection of documents to search through.
    n:
        Number of documents to retrieve per entity.
    client:
        Authenticated ``OpenAI`` or ``AzureOpenAI`` instance.
    chat_model:
        Chat completion model used for entity extraction.
    embedding_model:
        Embedding model used for semantic document retrieval.

    Returns
    -------
    dict[str, list[str]]
        Mapping of entity name → top-*n* matching documents from *corpus*.
    """
    entities = extract_entities(source_document, client, chat_model)
    return {
        entity: search_documents_by_entity(entity, corpus, n, client, embedding_model)
        for entity in entities
    }
