"""Unit tests for Groq-backed answer generation."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from src.rag.generator import generate_answer
from src.rag.retriever import RetrievalResult


def _retrieval() -> RetrievalResult:
    return RetrievalResult(
        chunks=[
            {
                "text": "Expense ratio 0.83%",
                "scheme_name": "HDFC Defence Fund Direct Growth",
                "section": "summary",
            }
        ],
        citation_chunk={
            "source_url": "https://groww.in/mutual-funds/hdfc-defence-fund-direct-growth",
        },
        structured_price=None,
        detected_scheme=None,
        insufficient_context=False,
        needs_disambiguation=False,
        ingested_at="2026-06-08T07:27:03.556464+00:00",
    )


@patch("src.rag.generator.GROQ_API_KEY", "")
def test_generate_answer_requires_groq_api_key() -> None:
    with pytest.raises(RuntimeError, match="GROQ_API_KEY"):
        generate_answer("What is the expense ratio?", _retrieval())


@patch("src.rag.generator._call_groq_llm")
def test_generate_answer_returns_llm_text(mock_call) -> None:
    mock_call.return_value = "The expense ratio is 0.83%."
    answer = generate_answer(
        "What is the expense ratio of HDFC Defence Fund Direct Growth?",
        _retrieval(),
    )
    assert answer == "The expense ratio is 0.83%."
    mock_call.assert_called_once()


@patch("groq.Groq")
@patch("src.rag.generator.GROQ_API_KEY", "gsk-test")
@patch("src.rag.generator.LLM_PROVIDER", "groq")
@patch("src.rag.generator.LLM_MODEL", "llama-3.3-70b-versatile")
def test_call_groq_uses_configured_model(mock_groq_cls) -> None:
    from src.rag.generator import _call_groq_llm

    mock_client = MagicMock()
    mock_groq_cls.return_value = mock_client
    mock_client.chat.completions.create.return_value = MagicMock(
        choices=[MagicMock(message=MagicMock(content="Answer text."))]
    )

    result = _call_groq_llm("Question: test\n\nContext:\nchunk")

    assert result == "Answer text."
    mock_client.chat.completions.create.assert_called_once()
    assert (
        mock_client.chat.completions.create.call_args.kwargs["model"]
        == "llama-3.3-70b-versatile"
    )
