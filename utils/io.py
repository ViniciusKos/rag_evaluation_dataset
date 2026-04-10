from __future__ import annotations

import json
import sys
from pathlib import Path


def load_documents(input_dir: Path) -> list[dict]:
    """Load all .json files in *input_dir* and return them as a list of dicts."""
    files = sorted(input_dir.glob("*.json"))
    if not files:
        print(f"[warning] No .json files found in '{input_dir}'.", file=sys.stderr)
        return []
    documents: list[dict] = []
    for path in files:
        with path.open(encoding="utf-8") as fh:
            documents.append(json.load(fh))
    print(f"[info] Loaded {len(documents)} document(s) from '{input_dir}'.")
    return documents


def build_corpus_texts(documents: list[dict], search_fields: list[str]) -> list[str]:
    """Concatenate *search_fields* values for each document into a single string."""
    texts: list[str] = []
    for doc in documents:
        text = "\n".join(
            str(doc[field]) for field in search_fields if field in doc
        ).strip()
        texts.append(text)
    return texts
