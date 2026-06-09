"""Unit tests for hybrid retrieval and reranking."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from src.config import CORPUS_BY_LOCAL_FILE
from src.rag.classifier import ClassificationResult, Intent, classify
from src.rag.retriever import (
    _build_structured_price,
    _detect_ambiguity,
    rerank_candidates,
    retrieve,
)


def _chunk(
    *,
    scheme_name: str,
    section: str,
    score: float,
    text: str = "sample text",
) -> dict:
    entry = next(item for item in CORPUS_BY_LOCAL_FILE.values() if item.scheme_name == scheme_name)
    return {
        "chunk_id": f"{entry.local_file}:{section}:0",
        "text": text,
        "source_url": entry.source_url,
        "scheme_name": scheme_name,
        "product_type": entry.product_type,
        "section": section,
        "local_file": entry.local_file,
        "ingested_at": "2026-06-08T07:27:03.556464+00:00",
        "score": score,
    }


def test_rerank_prefers_detected_scheme() -> None:
    classification = classify("exit load on HDFC Defence Fund")
    candidates = [
        _chunk(scheme_name="HDFC Mid Cap Fund Direct Growth", section="exit_load", score=0.82),
        _chunk(scheme_name="HDFC Defence Fund Direct Growth", section="exit_load", score=0.80),
    ]
    ranked = rerank_candidates(candidates, query="exit load on HDFC Defence Fund", classification=classification)
    assert ranked[0]["scheme_name"] == "HDFC Defence Fund Direct Growth"
    assert ranked[0]["adjusted_score"] > ranked[1]["adjusted_score"]


def test_rerank_prefers_section_for_benchmark_query() -> None:
    classification = classify("benchmark index for HDFC Defence Fund")
    candidates = [
        _chunk(scheme_name="HDFC Defence Fund Direct Growth", section="summary", score=0.85),
        _chunk(
            scheme_name="HDFC Defence Fund Direct Growth",
            section="about",
            score=0.80,
            text="Fund benchmarkNifty India Defence Total Return Index",
        ),
    ]
    ranked = rerank_candidates(
        candidates,
        query="benchmark index for HDFC Defence Fund",
        classification=classification,
    )
    assert ranked[0]["section"] == "about"


def test_detect_ambiguity_when_top_schemes_are_close() -> None:
    ranked = [
        {"local_file": "a.md", "adjusted_score": 0.72},
        {"local_file": "b.md", "adjusted_score": 0.70},
    ]
    assert _detect_ambiguity(ranked, scheme=None) is True


def test_detect_scheme_matches_fund_of_fund_phrase() -> None:
    from src.config import detect_scheme

    scheme = detect_scheme("minimum SIP for HDFC Gold ETF Fund of Fund")
    assert scheme is not None
    assert scheme.scheme_name == "HDFC Gold ETF Fund of Fund Direct Plan Growth"


def test_structured_price_contains_absolute_change() -> None:
    snapshot = {
        "scheme_name": "HDFC Silver ETF",
        "source_url": "https://groww.in/etfs/hdfc-silver-etf",
        "local_file": "hdfc-silver-etf-6.md",
        "product_type": "etf",
        "current_price": 243.53,
        "change_1d_abs": -3.16,
        "change_1d_pct": -1.28,
    }
    structured = _build_structured_price(snapshot)
    assert structured["change_1d_abs"] == -3.16
    assert "-3.16" in structured["text"]


@patch("src.rag.retriever.search_index")
def test_retrieve_injects_structured_price_for_nav_query(mock_search) -> None:
    defence = CORPUS_BY_LOCAL_FILE["hdfc-defence-fund-direct-growth.md"]
    mock_search.return_value = [
        {
            "chunk_id": "hdfc-defence-fund-direct-growth.md:summary:0",
            "text": "NAV hero chunk",
            "source_url": defence.source_url,
            "scheme_name": defence.scheme_name,
            "product_type": defence.product_type,
            "section": "summary",
            "local_file": defence.local_file,
            "ingested_at": "2026-06-08T07:27:03.556464+00:00",
            "score": 0.81,
        }
    ]
    classification = classify("What is the latest NAV of HDFC Defence Fund Direct Growth?")
    result = retrieve("What is the latest NAV of HDFC Defence Fund Direct Growth?", classification)
    assert result.structured_price is not None
    assert result.structured_price["nav"] == 28.72
    assert result.chunks[0]["section"] == "structured_price"


@patch("src.rag.retriever.search_index")
def test_retrieve_marks_insufficient_context_when_no_hits(mock_search) -> None:
    mock_search.return_value = []
    classification = classify("What is the expense ratio of HDFC Top 100 Fund?")
    result = retrieve("What is the expense ratio of HDFC Top 100 Fund?", classification)
    assert result.insufficient_context is True
    assert result.chunks == []
