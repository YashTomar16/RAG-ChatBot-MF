"""Phase 7 functional test matrix — routing and response categories."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from src.rag.pipeline import answer_query
from src.rag.retriever import RetrievalResult
from src.refusal.handler import route_query
from src.validation.compliance import (
    validate_factual_response,
    validate_performance_deflection,
    validate_refusal_response,
)

# --- 7 example FAQ questions from ProblemStatement / implementation plan ---
EXAMPLE_FAQ = [
    (
        "What is the expense ratio of HDFC Defence Fund Direct Growth?",
        "0.83",
    ),
    (
        "What is the minimum SIP for HDFC Gold ETF FoF?",
        "100",
    ),
    (
        "What is the exit load on HDFC Silver ETF FoF Direct Growth?",
        "1%",
    ),
    (
        "What is the benchmark index for HDFC Defence Fund?",
        "Defence",
    ),
    (
        "What is the risk category of HDFC Balanced Advantage Fund?",
        "Very High",
    ),
    (
        "What is the latest NAV of HDFC Defence Fund Direct Growth?",
        "28.72",
    ),
    (
        "What is the 1-day change for HDFC Silver ETF?",
        "-3.16",
    ),
]

REFUSAL_QUERIES = [
    "Should I invest in this fund?",
    "Which fund is better?",
]

PERFORMANCE_QUERIES = [
    "What returns did this fund give?",
    "What is the 3Y CAGR of HDFC Defence Fund?",
]

OUT_OF_SCOPE_QUERIES = [
    "What is the weather?",
]

AMBIGUOUS_QUERIES = [
    "HDFC fund expense ratio",
]

INSUFFICIENT_CONTEXT_QUERIES = [
    "What is the ELSS lock-in period for HDFC ELSS?",
]


@pytest.mark.parametrize("query", REFUSAL_QUERIES)
def test_matrix_advisory_and_comparison_refused(query: str) -> None:
    route = route_query(query)
    assert route.proceed_to_rag is False
    assert route.response is not None
    result = validate_refusal_response(route.response)
    assert result.ok, result.errors


@pytest.mark.parametrize("query", PERFORMANCE_QUERIES)
def test_matrix_performance_deflection(query: str) -> None:
    route = route_query(query)
    assert route.proceed_to_rag is False
    assert route.response is not None
    result = validate_performance_deflection(route.response)
    assert result.ok, result.errors


@pytest.mark.parametrize("query", OUT_OF_SCOPE_QUERIES)
def test_matrix_out_of_scope(query: str) -> None:
    route = route_query(query)
    assert route.proceed_to_rag is False
    assert route.response is not None
    assert "factual" in route.response.lower() or "can only help" in route.response.lower()


@pytest.mark.parametrize("query", AMBIGUOUS_QUERIES)
def test_matrix_ambiguous_scheme_routes_to_rag(query: str) -> None:
    route = route_query(query)
    assert route.proceed_to_rag is True


@pytest.mark.parametrize("query", INSUFFICIENT_CONTEXT_QUERIES)
def test_matrix_insufficient_context_proceeds_to_rag(query: str) -> None:
    """ELSS not in corpus — factual intent but generator should fall back."""
    route = route_query(query)
    assert route.proceed_to_rag is True


@pytest.mark.parametrize("query,expected_snippet", EXAMPLE_FAQ)
@patch("src.rag.pipeline.generate_answer")
@patch("src.rag.pipeline.retrieve")
def test_matrix_example_faq_formatted(mock_retrieve, mock_generate, query, expected_snippet) -> None:
    mock_retrieve.return_value = RetrievalResult(
        chunks=[{"text": f"Fact containing {expected_snippet}", "section": "summary"}],
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
    mock_generate.return_value = f"The answer includes {expected_snippet}."
    response = answer_query(query)
    compliance = validate_factual_response(response)
    assert compliance.ok, compliance.errors
    assert expected_snippet.lower() in response.lower() or expected_snippet in response


def test_matrix_price_nav_queries_route_to_rag() -> None:
    price_queries = [
        "Latest NAV of HDFC Defence",
        "1-day change HDFC Silver ETF",
        "HDFC Bank share price",
    ]
    for query in price_queries:
        route = route_query(query)
        assert route.proceed_to_rag is True, query


@patch("src.rag.pipeline.generate_answer")
@patch("src.rag.pipeline.retrieve")
def test_matrix_insufficient_context_fallback(mock_retrieve, mock_generate) -> None:
    mock_retrieve.return_value = RetrievalResult(
        chunks=[],
        citation_chunk={"source_url": "https://groww.in/mutual-funds/hdfc-defence-fund-direct-growth"},
        structured_price=None,
        detected_scheme=None,
        insufficient_context=True,
        needs_disambiguation=False,
        ingested_at="2026-06-08T07:27:03.556464+00:00",
    )
    mock_generate.return_value = "I don't have enough information in the ingested Groww corpus."
    response = answer_query("What is the ELSS lock-in period for HDFC ELSS?")
    assert "enough information" in response.lower()
