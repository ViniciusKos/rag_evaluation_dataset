from __future__ import annotations

import json
from unittest.mock import MagicMock

import pytest

from src.entity_search import extract_entities


def _make_client(entities: list[str]) -> MagicMock:
    """Return a mock LLM client that always responds with *entities*."""
    payload = json.dumps({"entities": entities})
    message = MagicMock()
    message.content = payload
    choice = MagicMock()
    choice.message = message
    response = MagicMock()
    response.choices = [choice]
    client = MagicMock()
    client.chat.completions.create.return_value = response
    return client


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------

class TestExtractEntitiesHappyPath:
    def test_returns_entities_from_search_fields(self):
        client = _make_client(["Albert Einstein", "Germany"])
        doc = {"id": "1", "title": "Albert Einstein", "body": "German physicist"}
        result = extract_entities(doc, search_fields=["title", "body"], client=client)
        assert result == ["Albert Einstein", "Germany"]

    def test_only_search_fields_are_sent_to_llm(self):
        client = _make_client(["NASA"])
        doc = {"id": "meta_id", "source": "wikipedia", "body": "NASA launched a rocket"}
        extract_entities(doc, search_fields=["body"], client=client)
        call_messages = client.chat.completions.create.call_args.kwargs["messages"]
        user_content = next(m["content"] for m in call_messages if m["role"] == "user")
        assert "NASA launched a rocket" in user_content
        assert "meta_id" not in user_content
        assert "wikipedia" not in user_content

    def test_multiple_search_fields_are_joined(self):
        client = _make_client([])
        doc = {"title": "Hello", "summary": "World"}
        extract_entities(doc, search_fields=["title", "summary"], client=client)
        call_messages = client.chat.completions.create.call_args.kwargs["messages"]
        user_content = next(m["content"] for m in call_messages if m["role"] == "user")
        assert "Hello" in user_content
        assert "World" in user_content

    def test_uses_provided_model(self):
        client = _make_client([])
        doc = {"body": "Some text"}
        extract_entities(doc, search_fields=["body"], client=client, model="gpt-4o")
        called_model = client.chat.completions.create.call_args.kwargs["model"]
        assert called_model == "gpt-4o"


# ---------------------------------------------------------------------------
# Missing / empty fields
# ---------------------------------------------------------------------------

class TestExtractEntitiesMissingFields:
    def test_missing_search_field_is_ignored(self):
        client = _make_client(["Entity"])
        doc = {"body": "Some text"}
        # "title" is not in doc — should not raise, just skip it
        result = extract_entities(doc, search_fields=["title", "body"], client=client)
        assert result == ["Entity"]
        client.chat.completions.create.assert_called_once()

    def test_all_search_fields_missing_returns_empty_list(self):
        client = _make_client(["Entity"])
        doc = {"id": "1", "source": "web"}
        result = extract_entities(doc, search_fields=["title", "body"], client=client)
        assert result == []
        client.chat.completions.create.assert_not_called()

    def test_empty_search_fields_list_returns_empty_list(self):
        client = _make_client(["Entity"])
        doc = {"body": "Some text"}
        result = extract_entities(doc, search_fields=[], client=client)
        assert result == []
        client.chat.completions.create.assert_not_called()

    def test_blank_field_values_return_empty_list(self):
        client = _make_client(["Entity"])
        doc = {"title": "   ", "body": "\n\t"}
        result = extract_entities(doc, search_fields=["title", "body"], client=client)
        assert result == []
        client.chat.completions.create.assert_not_called()


# ---------------------------------------------------------------------------
# LLM response edge cases
# ---------------------------------------------------------------------------

class TestExtractEntitiesLLMResponse:
    def test_llm_returns_empty_entities_list(self):
        client = _make_client([])
        doc = {"body": "No named entities here"}
        result = extract_entities(doc, search_fields=["body"], client=client)
        assert result == []

    def test_llm_returns_none_content_treated_as_empty(self):
        message = MagicMock()
        message.content = None
        choice = MagicMock()
        choice.message = message
        response = MagicMock()
        response.choices = [choice]
        client = MagicMock()
        client.chat.completions.create.return_value = response

        doc = {"body": "Some text"}
        result = extract_entities(doc, search_fields=["body"], client=client)
        assert result == []

    def test_llm_returns_json_without_entities_key(self):
        message = MagicMock()
        message.content = json.dumps({"other_key": ["value"]})
        choice = MagicMock()
        choice.message = message
        response = MagicMock()
        response.choices = [choice]
        client = MagicMock()
        client.chat.completions.create.return_value = response

        doc = {"body": "Some text"}
        result = extract_entities(doc, search_fields=["body"], client=client)
        assert result == []
