from __future__ import annotations

import argparse
from pathlib import Path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate QA pairs from a JSON file containing multiple records.",
    )
    parser.add_argument(
        "--input-file",
        required=True,
        type=str,
        help=(
            "Path to a JSON file containing a list of document records. "
            "Accepts a local path or a remote URI "
            "(e.g. az://container/docs.json, s3://bucket/docs.json)."
        ),
    )
    parser.add_argument(
        "--search-fields",
        required=True,
        nargs="+",
        metavar="FIELD",
        help="Document fields used for entity extraction and corpus building.",
    )
    parser.add_argument(
        "--output",
        required=True,
        type=Path,
        help="Path to the output JSON file.",
    )
    parser.add_argument(
        "--client",
        choices=["openai", "azure"],
        default="openai",
        help="LLM provider (default: openai).",
    )
    parser.add_argument(
        "--model",
        default="gpt-4o-mini",
        help="Chat model for entity extraction and QA generation (default: gpt-4o-mini).",
    )
    parser.add_argument(
        "--embedding-model",
        default="text-embedding-3-small",
        help="Embedding model for semantic search (default: text-embedding-3-small).",
    )
    parser.add_argument(
        "--top-n",
        type=int,
        default=3,
        help="Number of documents to retrieve per entity via embedding search (default: 3).",
    )
    return parser
