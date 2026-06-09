"""Unit tests for end-to-end pipeline routing."""

from __future__ import annotations

from unittest.mock import patch

from src.rag.pipeline import answer_query
from src.rag.retriever import RetrievalResult


def test_pipeline_refuses_advisory_query() -> None:
    response = answer_query("Should I invest in HDFC Gold ETF FoF?")
    assert "factual questions" in response.lower()
    assert "amfiindia.com" in response


@patch("src.rag.pipeline.generate_answer")
@patch("src.rag.pipeline.retrieve")
def test_pipeline_formats_factual_answer(mock_retrieve, mock_generate) -> None:
    mock_retrieve.return_value = RetrievalResult(
        chunks=[{"text": "Expense ratio 0.83%", "section": "summary"}],
        citation_chunk={
            "source_url": "https://groww.in/mutual-funds/hdfc-defence-fund-direct-growth",
            "nav_date": "2026-06-05",
        },
        structured_price=None,
        detected_scheme=None,
        insufficient_context=False,
        needs_disambiguation=False,
        ingested_at="2026-06-08T07:27:03.556464+00:00",
    )
    mock_generate.return_value = "The expense ratio of HDFC Defence Fund Direct Growth is 0.83%."
    response = answer_query("What is the expense ratio of HDFC Defence Fund Direct Growth?")
    assert "0.83%" in response
    assert "groww.in/mutual-funds/hdfc-defence-fund-direct-growth" in response
    assert "Last updated from sources:" in response


def test_pipeline_rejects_empty_query() -> None:
    response = answer_query("   ")
    assert "enter a factual question" in response.lower()
