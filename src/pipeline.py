"""End-to-end QA-pairs generation pipeline.

Usage (installed command)
-------------------------
qa-generate \\
    --input-file ./docs/documents.json \\
    --search-fields title description \\
    --output     qa_output.json \\
    [--client    openai|azure] \\
    [--model     gpt-4o-mini] \\
    [--embedding-model text-embedding-3-small] \\
    [--top-n     3]

Usage (script)
--------------
python run_pipeline.py <same flags>
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from src.embedding_search import find_top_n_similar, get_embeddings
from src.entity_search import entity_document_search
from src.generate_qa_pairs import QAPair, generate_qa_pairs
from src.llm_factory import LLMClient, create_azure_openai_client, create_openai_client
from utils.cli import build_parser
from utils.entities import extract_all_entities
from utils.io import build_corpus_texts, load_documents

# ── Pipeline ─────────────────────────────────────────────────────────────────


def run_pipeline(
    input_file: str | Path,
    search_fields: list[str],
    output: Path,
    *,
    client_type: str = "openai",
    model: str = "gpt-4o-mini",
    embedding_model: str = "text-embedding-3-small",
    top_n: int = 3,
) -> list[QAPair]:
    # ── 1. LLM client ────────────────────────────────────────────────────────
    client: LLMClient
    if client_type == "azure":
        client = create_azure_openai_client()
    else:
        client = create_openai_client()

    # ── 2. Load documents & build corpus ─────────────────────────────────────
    documents = load_documents(input_file)
    if not documents:
        print("[warning] No documents to process. Exiting.", file=sys.stderr)
        return []

    corpus_texts = build_corpus_texts(documents, search_fields)

    # ── 3. Extract entities ───────────────────────────────────────────────────
    print("[info] Extracting entities from documents…")
    entities = extract_all_entities(documents, search_fields, client, model)
    if not entities:
        print("[warning] No entities extracted. Exiting.", file=sys.stderr)
        return []

    # ── 4. Hybrid entity-document search ─────────────────────────────────────
    print("[info] Running hybrid entity-document search…")

    # Keyword pass
    keyword_results = entity_document_search(entities, corpus_texts)

    # Embedding pass
    all_embeddings = get_embeddings(
        corpus_texts + entities, client, model=embedding_model
    )
    corpus_embeddings = all_embeddings[: len(corpus_texts)]
    entity_embeddings = all_embeddings[len(corpus_texts) :]

    # Merge: keyword-first, deduplicated
    entity_documents: dict[str, list[str]] = {}
    for entity, entity_emb in zip(entities, entity_embeddings):
        top_indices = find_top_n_similar(entity_emb, corpus_embeddings, n=top_n)
        embedding_docs = [corpus_texts[i] for i in top_indices]
        seen: set[str] = set()
        combined: list[str] = []
        for doc in keyword_results.get(entity, []) + embedding_docs:
            if doc not in seen:
                seen.add(doc)
                combined.append(doc)
        entity_documents[entity] = combined
    total_pairs = sum(len(docs) for docs in entity_documents.values())
    print(f"[info] {total_pairs} (entity, document) pair(s) to process.")

    # ── 5. Generate QA pairs ──────────────────────────────────────────────────
    print("[info] Generating QA pairs…")
    qa_pairs = generate_qa_pairs(entity_documents, client, model=model)
    print(f"[info] Generated {len(qa_pairs)} QA pair(s).")

    # ── 6. Write output ───────────────────────────────────────────────────────
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as fh:
        json.dump(qa_pairs, fh, ensure_ascii=False, indent=2)
    print(f"[info] Output written to '{output}'.")

    return qa_pairs


# ── Entry point ──────────────────────────────────────────────────────────────


def main() -> None:
    args = build_parser().parse_args()
    run_pipeline(
        input_file=args.input_file,
        search_fields=args.search_fields,
        output=args.output,
        client_type=args.client,
        model=args.model,
        embedding_model=args.embedding_model,
        top_n=args.top_n,
    )
