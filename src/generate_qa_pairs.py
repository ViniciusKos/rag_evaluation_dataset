from __future__ import annotations

import json
from pathlib import Path
from typing import TypedDict

from tqdm import tqdm

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
    model: str = "gpt-5.4-mini",
    n_questions_per_entity: int = 3,
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

    with tqdm(
        total=len(entity_documents), desc="Generating QA pairs", unit="entity"
    ) as pbar:
        for entity, documents in entity_documents.items():
            combined_document = "\n\n---\n\n".join(documents)
            user_message = (
                f"Entity: {entity}\n\n"
                f"Document:\n{combined_document}\n\n"
                f"N: {n_questions_per_entity}"
            )

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
            parsed = json.loads(raw)

            for pair in parsed.get("pairs", [])[:n_questions_per_entity]:
                qa_pairs.append(
                    QAPair(
                        entity=entity,
                        question=pair.get("question", ""),
                        answer=pair.get("answer", ""),
                        source_document=combined_document,
                    )
                )
            pbar.set_postfix(entity=entity)
            pbar.update(1)

    return qa_pairs
