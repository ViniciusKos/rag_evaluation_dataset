from __future__ import annotations

import json
import os
from pathlib import Path

import fsspec  # type: ignore[import-untyped]

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
            from azure.identity import DefaultAzureCredential  # type: ignore[import-not-found]
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


def load_documents(input_file: str | Path) -> list[dict]:
    """Load a single JSON file containing a list of document records.

    *input_file* can be a local path or a remote URI supported by fsspec:
    - Local:        ``./data/docs.json`` or ``/abs/path/docs.json``
    - Azure Blob:   ``az://container/docs.json``
    - S3:           ``s3://bucket/docs.json``
    - GCS:          ``gcs://bucket/docs.json``

    The file must contain a JSON array of objects, e.g.::

        [
            {"id": "1", "title": "Doc A", ...},
            {"id": "2", "title": "Doc B", ...}
        ]

    Azure authentication is resolved from environment variables (see
    ``_azure_storage_options`` for priority order).
    """
    path = str(input_file)
    options = _storage_options(path)

    with fsspec.open(path, "r", encoding="utf-8", **options) as fh:
        data = json.load(fh)

    if not isinstance(data, list):
        raise ValueError(
            f"Expected a JSON array in '{input_file}', got {type(data).__name__}."
        )

    print(f"[info] Loaded {len(data)} document(s) from '{input_file}'.")
    return data


def build_corpus_texts(documents: list[dict], search_fields: list[str]) -> list[str]:
    """Concatenate *search_fields* values for each document into a single string."""
    texts: list[str] = []
    for doc in documents:
        text = "\n".join(
            str(doc[field]) for field in search_fields if field in doc
        ).strip()
        texts.append(text)
    return texts
