"""Optional integration tests — require built index; live tests need RUN_LIVE_INTEGRATION=1."""

from __future__ import annotations

import os

import pytest

from src.api.service import index_ready
from src.config import load_price_snapshot
from src.validation.compliance import validate_factual_response

pytestmark = pytest.mark.skipif(not index_ready(), reason="index/ not built")

RUN_LIVE = os.getenv("RUN_LIVE_INTEGRATION", "").lower() in ("1", "true", "yes")


@pytest.mark.skipif(not RUN_LIVE, reason="Set RUN_LIVE_INTEGRATION=1 for live retrieval test")
def test_integration_retriever_finds_defence_expense_ratio() -> None:
    from src.rag.classifier import classify
    from src.rag.retriever import retrieve

    query = "What is the expense ratio of HDFC Defence Fund Direct Growth?"
    classification = classify(query)
    result = retrieve(query, classification)
    assert result.chunks
    assert any("Defence" in chunk.get("scheme_name", "") for chunk in result.chunks)
    assert result.citation_chunk.get("source_url", "").startswith("https://groww.in/")


def test_integration_price_snapshot_nav_for_defence() -> None:
    row = load_price_snapshot("hdfc-defence-fund-direct-growth.md")
    assert row is not None
    assert row["nav"] == 28.72


@pytest.mark.skipif(not RUN_LIVE, reason="Set RUN_LIVE_INTEGRATION=1 for live LLM test")
@pytest.mark.skipif(not os.getenv("GROQ_API_KEY"), reason="GROQ_API_KEY required for live LLM")
def test_integration_live_pipeline_defence_expense_ratio() -> None:
    from src.rag.pipeline import answer_query

    response = answer_query("What is the expense ratio of HDFC Defence Fund Direct Growth?")
    compliance = validate_factual_response(response)
    assert compliance.ok, compliance.errors
    assert "0.83" in response
