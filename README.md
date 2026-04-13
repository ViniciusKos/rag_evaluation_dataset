# QA Pairs Generator for RAG Evaluation

Automatically generate question-answer pairs from a corpus of JSON documents to evaluate Retrieval-Augmented Generation (RAG) pipelines. The tool extracts named entities from your documents, matches each entity to its most relevant documents via hybrid search (keyword + embeddings), and then prompts an LLM to produce one QA pair per (entity, document) combination.

---

## Table of contents

- [Installation](#installation)
- [Input document format](#input-document-format)
- [Environment variables](#environment-variables)
- [Usage](#usage)
- [Remote storage](#remote-storage)
- [Output format](#output-format)

---

## Installation

Requires **Python ≥ 3.10**.

### With pip

```bash
# runtime only
pip install -e .

# runtime + dev dependencies (pytest)
pip install -e ".[dev]"

# runtime + Azure Blob Storage support
pip install -e ".[azure]"
```

### With uv

```bash
uv sync                    # runtime only
uv sync --extra dev        # include dev dependencies
uv sync --extra azure      # include Azure Blob Storage support
```

After installing, the `qa-generate` console script is available as an alternative to `python run_pipeline.py`.

---

## Input document format

The input must be a **single `.json` file** containing a JSON array of document records. Each record can have any top-level fields; you tell the pipeline which ones to use via `--search-fields`.

Minimal example (`data/documents.json`):

```json
[
  {
    "title": "Introduction to Transformers",
    "description": "Transformers are a type of neural network architecture introduced in the paper Attention Is All You Need.",
    "author": "Vaswani et al.",
    "year": 2017
  },
  {
    "title": "BERT: Pre-training of Deep Bidirectional Transformers",
    "description": "BERT is designed to pre-train deep bidirectional representations from unlabeled text.",
    "author": "Devlin et al.",
    "year": 2018
  }
]
```

If you run the pipeline with `--search-fields title description`, the tool will concatenate the `title` and `description` fields to build the corpus text used for entity extraction and search. Fields listed in `--search-fields` that are absent from a document are silently skipped.

---

## Environment variables

### OpenAI (default)

| Variable | Required | Description |
|---|---|---|
| `OPENAI_API_KEY` | Yes | Your OpenAI secret key |

### Azure OpenAI (`--client azure`)

| Variable | Required | Description |
|---|---|---|
| `AZURE_OPENAI_API_KEY` | Yes | Your Azure OpenAI key |
| `AZURE_OPENAI_ENDPOINT` | Yes | Your Azure endpoint URL (e.g. `https://<resource>.openai.azure.com/`) |
| `OPENAI_API_VERSION` | Yes | API version (e.g. `2024-02-01`) |

### Azure Blob Storage (`az://` input URIs)

The following variables are resolved in priority order:

| Priority | Variable(s) | Description |
|---|---|---|
| 1 | `AZURE_STORAGE_CONNECTION_STRING` | Full connection string |
| 2 | `AZURE_STORAGE_ACCOUNT_NAME` + `AZURE_STORAGE_ACCOUNT_KEY` | Account name and key |
| 3 | `AZURE_STORAGE_ACCOUNT_NAME` (only) | Uses `DefaultAzureCredential` (managed identity, Azure CLI, workload identity, etc.) |

You can export the variables in your shell or store them in a `.env` file and load it before running the pipeline.

```bash
# Linux / macOS
export OPENAI_API_KEY="sk-..."

# Windows PowerShell
$env:OPENAI_API_KEY = "sk-..."
```

---

## Usage

The pipeline can be invoked either via the installed script or directly:

```bash
# installed command
qa-generate --input-file <FILE.json> --search-fields <FIELD ...> --output <FILE.json> [options]

# or via script
python run_pipeline.py --input-file <FILE.json> --search-fields <FIELD ...> --output <FILE.json> [options]
```

| Argument | Required | Default | Description |
|---|---|---|---|
| `--input-file` | Yes | — | Local path **or** remote URI (e.g. `az://container/docs.json`, `s3://bucket/docs.json`) to a JSON file containing a list of document records |
| `--search-fields` | Yes | — | One or more document fields to use for entity extraction and corpus building |
| `--output` | Yes | — | Path to the output JSON file |
| `--client` | No | `openai` | LLM provider: `openai` or `azure` |
| `--model` | No | `gpt-5.4-mini` | Chat model used for entity extraction and QA generation |
| `--embedding-model` | No | `text-embedding-3-small` | Embedding model used for semantic search |
| `--top-n` | No | `3` | Number of documents retrieved per entity via embedding search |
| `--questions-per-entity` | No | `3` | Number of questions to generate per entity |

### Complete example

```bash
python run_pipeline.py \
    --input-file  ./data/documents.json \
    --search-fields title description \
    --output      qa_output.json \
    --client      openai \
    --model       gpt-5.4-mini \
    --embedding-model text-embedding-3-small \
    --top-n       3 \
    --questions-per-entity 3
```

### Azure OpenAI example

```bash
python run_pipeline.py \
    --input-file  ./data/documents.json \
    --search-fields title description \
    --output      qa_output.json \
    --client      azure \
    --model       my-gpt4o-deployment \
    --embedding-model my-embedding-deployment
```

---

## Remote storage

`--input-dir` accepts any URI supported by [fsspec](https://filesystem-spec.readthedocs.io/). The pipeline reads `.json` files transparently from:

| Scheme | Backend | Extra install |
|---|---|---|
| `./path/docs.json` or `/abs/path/docs.json` | Local filesystem | — |
| `az://container/docs.json` | Azure Blob Storage | `pip install -e ".[azure]"` |
| `s3://bucket/docs.json` | Amazon S3 | `pip install s3fs` |
| `gcs://bucket/docs.json` | Google Cloud Storage | `pip install gcsfs` |

```bash
# read documents from Azure Blob Storage
python run_pipeline.py \
    --input-file  az://my-container/corpus/documents.json \
    --search-fields title description \
    --output      qa_output.json
```

---

## Output format

The output is a JSON array. Each element is a QA pair with the following fields:

```json
[
  {
    "entity": "Transformers",
    "question": "What problem do Transformers solve compared to RNNs?",
    "answer": "Transformers solve the sequential computation bottleneck of RNNs by relying entirely on self-attention mechanisms, enabling parallelisation during training.",
    "source_document": "Introduction to Transformers\nTransformers are a type of neural network architecture..."
  }
]
```

| Field | Type | Description |
|---|---|---|
| `entity` | `string` | Named entity extracted from the documents |
| `question` | `string` | Generated question about the entity |
| `answer` | `string` | Generated answer grounded in the source document |
| `source_document` | `string` | Concatenated text of the document used to generate the pair |
