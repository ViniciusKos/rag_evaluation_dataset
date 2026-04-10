from __future__ import annotations

import math

from src.llm_factory import LLMClient


def get_embeddings(
    texts: list[str],
    client: LLMClient,
    model: str = "text-embedding-3-small",
) -> list[list[float]]:
    """Return one embedding vector per text using the OpenAI Embeddings API."""
    response = client.embeddings.create(input=texts, model=model)
    return [item.embedding for item in response.data]


def cosine_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    """Return the cosine similarity between two vectors."""
    dot = sum(a * b for a, b in zip(vec_a, vec_b))
    norm_a = math.sqrt(sum(a * a for a in vec_a))
    norm_b = math.sqrt(sum(b * b for b in vec_b))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return dot / (norm_a * norm_b)


def find_top_n_similar(
    query_embedding: list[float],
    corpus_embeddings: list[list[float]],
    n: int,
) -> list[int]:
    """Return the indices of the *n* corpus embeddings closest to *query_embedding*."""
    scores = [
        (idx, cosine_similarity(query_embedding, emb))
        for idx, emb in enumerate(corpus_embeddings)
    ]
    scores.sort(key=lambda pair: pair[1], reverse=True)
    return [idx for idx, _ in scores[:n]]
