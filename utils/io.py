from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import fsspec


# ── Authentication helpers ────────────────────────────────────────────────────


def _azure_storage_options() -> dict:
    """Resolve Azure Blob auth from environment variables.

    Priority:
    1. ``AZURE_STORAGE_CONNECTION_STRING``
    2. ``AZURE_STORAGE_ACCOUNT_NAME`` + ``AZURE_STORAGE_ACCOUNT_KEY``
    3. ``AZURE_STORAGE_ACCOUNT_NAME`` + ``DefaultAzureCredential``
       (managed identity, Azure CLI, workload identity, etc.)
    """
    conn_str = os.environ.get("AZURE_STORAGE_CONNECTION_STRING")
    if conn_str:
        return {"connection_string": conn_str}

    account_name = os.environ.get("AZURE_STORAGE_ACCOUNT_NAME")
    if account_name:
        account_key = os.environ.get("AZURE_STORAGE_ACCOUNT_KEY")
        if account_key:
            return {"account_name": account_name, "account_key": account_key}
        try:
            from azure.identity import DefaultAzureCredential  # type: ignore[import-untyped]
        except ImportError as exc:
            raise ImportError(
                "azure-identity is required for DefaultAzureCredential auth. "
                "Install it with: pip install azure-identity"
            ) from exc
        return {"account_name": account_name, "credential": DefaultAzureCredential()}

    return {}


def _storage_options(path: str) -> dict:
    if path.startswith(("az://", "abfs://", "abfss://")):
        return _azure_storage_options()
    return {}


# ── Public API ────────────────────────────────────────────────────────────────


def load_documents(input_dir: str | Path) -> list[dict]:
    """Load all .json files in *input_dir* and return them as a list of dicts.

    *input_dir* can be a local path or a remote URI supported by fsspec:
    - Local:        ``./data/`` or ``/abs/path/``
    - Azure Blob:   ``az://container/prefix/``
    - S3:           ``s3://bucket/prefix/``
    - GCS:          ``gcs://bucket/prefix/``

    Azure authentication is resolved from environment variables (see
    ``_azure_storage_options`` for priority order).
    """
    path = str(input_dir).rstrip("/\\")
    pattern = f"{path}/*.json"
    options = _storage_options(path)

    open_files = fsspec.open_files(pattern, "r", encoding="utf-8", **options)
    if not open_files:
        print(f"[warning] No .json files found in '{input_dir}'.", file=sys.stderr)
        return []

    documents: list[dict] = []
    for of in sorted(open_files, key=lambda f: f.path):
        with of as fh:
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
