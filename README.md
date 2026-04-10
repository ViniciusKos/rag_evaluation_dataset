# QA Pairs Generator for RAG Evaluation

Automatically generate question-answer pairs from a corpus of JSON documents to evaluate Retrieval-Augmented Generation (RAG) pipelines. The tool extracts named entities from your documents, matches each entity to its most relevant documents via hybrid search (keyword + embeddings), and then prompts an LLM to produce one QA pair per (entity, document) combination.

---

## Table of contents

- [Installation](#installation)
- [Input document format](#input-document-format)
- [Environment variables](#environment-variables)
- [Usage](#usage)
- [Output format](#output-format)

---

## Installation

Requires **Python ≥ 3.13**.

### With pip

```bash
# runtime only
pip install -e .

# runtime + dev dependencies (pytest)
pip install -e ".[dev]"
```

### With uv

```bash
uv sync          # runtime only
uv sync --extra dev   # include dev dependencies
```

---

## Input document format

Each document must be a **single `.json` file** inside the input directory. A document can have any top-level fields; you tell the pipeline which ones to use via `--search-fields`.

Minimal example (`docs/doc_001.json`):

```json
{
  "title": "Introduction to Transformers",
  "description": "Transformers are a type of neural network architecture introduced in the paper Attention Is All You Need.",
  "author": "Vaswani et al.",
  "year": 2017
}
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

You can export the variables in your shell or store them in a `.env` file and load it before running the pipeline.

```bash
# Linux / macOS
export OPENAI_API_KEY="sk-..."

# Windows PowerShell
$env:OPENAI_API_KEY = "sk-..."
```

---

## Usage

```
python run_pipeline.py \
    --input-dir   <DIR>          \
    --search-fields <FIELD ...>  \
    --output      <FILE.json>    \
    [--client     openai|azure]  \
    [--model      <MODEL>]       \
    [--embedding-model <MODEL>]  \
    [--top-n      <N>]
```

| Argument | Required | Default | Description |
|---|---|---|---|
| `--input-dir` | Yes | — | Directory containing `.json` input files |
| `--search-fields` | Yes | — | One or more document fields to use for entity extraction and corpus building |
| `--output` | Yes | — | Path to the output JSON file |
| `--client` | No | `openai` | LLM provider: `openai` or `azure` |
| `--model` | No | `gpt-4o-mini` | Chat model used for entity extraction and QA generation |
| `--embedding-model` | No | `text-embedding-3-small` | Embedding model used for semantic search |
| `--top-n` | No | `3` | Number of documents retrieved per entity via embedding search |

### Complete example

```bash
python run_pipeline.py \
    --input-dir   ./docs \
    --search-fields title description \
    --output      qa_output.json \
    --client      openai \
    --model       gpt-4o-mini \
    --embedding-model text-embedding-3-small \
    --top-n       3
```

### Azure OpenAI example

```bash
python run_pipeline.py \
    --input-dir   ./docs \
    --search-fields title description \
    --output      qa_output.json \
    --client      azure \
    --model       my-gpt4o-deployment \
    --embedding-model my-embedding-deployment
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
