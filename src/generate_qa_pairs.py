from __future__ import annotations

import json
from pathlib import Path
from typing import TypedDict

from src.llm_factory import LLMClient


class QAPair(TypedDict):
    entity: str
    question: str
    answer: str
    source_document: str


_SYSTEM_PROMPT = (
    Path(__file__).parent / "prompts" / "generate_qa_pairs_system.md"
).read_text(encoding="utf-8")


def generate_qa_pairs(
    entity_documents: dict[str, list[str]],
    client: LLMClient,
    model: str = "gpt-4o-mini",
) -> list[QAPair]:
    """Generate QA pairs for every (entity, document) combination.

    Parameters
    ----------
    entity_documents:
        Mapping of entity name -> list of document strings.
    client:
        Authenticated :class:`openai.OpenAI` or :class:`openai.AzureOpenAI` instance.
    model:
        OpenAI chat model to use.

    Returns
    -------
    list[QAPair]
        One QA pair per document, enriched with the entity name and the
        original document text.
    """
    qa_pairs: list[QAPair] = []

    for entity, documents in entity_documents.items():
        combined_document = "\n\n---\n\n".join(documents)
        user_message = f"Entity: {entity}\n\nDocument:\n{combined_document}"
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ],
            response_format={"type": "json_object"},
            temperature=0.2,
        )

        raw = response.choices[0].message.content or "{}"
        parsed: dict[str, str] = json.loads(raw)

        qa_pairs.append(
            QAPair(
                entity=entity,
                question=parsed.get("question", ""),
                answer=parsed.get("answer", ""),
                source_document=combined_document,
            )
        )

    return qa_pairs
