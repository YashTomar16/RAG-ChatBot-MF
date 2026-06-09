"""Unit tests for query intent classification and refusal routing."""

from __future__ import annotations

import pytest

from src.config import detect_scheme
from src.rag.classifier import Intent, classify
from src.refusal.handler import (
    AMFI_INVESTOR_CORNER,
    SEBI_INVESTOR_EDUCATION,
    route_query,
)


@pytest.mark.parametrize(
    ("query", "expected_intent"),
    [
        ("Should I invest in HDFC Gold ETF FoF?", Intent.ADVISORY),
        ("Is HDFC Defence Fund a good investment?", Intent.ADVISORY),
        ("What is the expense ratio and should I buy it?", Intent.ADVISORY),
        ("What fund do you recommend for retirement?", Intent.ADVISORY),
        ("Which fund is better?", Intent.COMPARISON),
        (
            "Which fund is better — HDFC Defence or HDFC Mid Cap?",
            Intent.COMPARISON,
        ),
        ("Compare expense ratios of HDFC Defence and HDFC Mid Cap", Intent.COMPARISON),
        ("Rank HDFC funds by expense ratio", Intent.COMPARISON),
        ("What returns did HDFC Defence give last year?", Intent.PERFORMANCE),
        ("What is the CAGR of HDFC Small Cap Fund?", Intent.PERFORMANCE),
        ("What is the 3Y annualised return for HDFC Mid Cap?", Intent.PERFORMANCE),
        ("What is the latest NAV of HDFC Defence Fund?", Intent.FACTUAL_PRICE),
        ("What is the 1-day change for HDFC Silver ETF?", Intent.FACTUAL_PRICE),
        ("HDFC Bank share price", Intent.FACTUAL_PRICE),
        (
            "What is the expense ratio of HDFC Defence Fund Direct Growth?",
            Intent.FACTUAL,
        ),
        ("What is the expense ratio?", Intent.FACTUAL),
        ("Show me exit load for Defence Fund", Intent.FACTUAL),
        ("Tell me about HDFC Bank stock", Intent.FACTUAL),
        ("What is the weather today?", Intent.OUT_OF_SCOPE),
        ("", Intent.OUT_OF_SCOPE),
    ],
)
def test_classify_intent(query: str, expected_intent: Intent) -> None:
    result = classify(query)
    assert result.intent == expected_intent


def test_factual_queries_proceed_to_rag() -> None:
    factual_queries = (
        "What is the expense ratio of HDFC Defence Fund Direct Growth?",
        "What is the latest NAV of HDFC Defence Fund?",
        "What is the 1-day change for HDFC Silver ETF?",
    )
    for query in factual_queries:
        result = route_query(query)
        assert result.proceed_to_rag is True
        assert result.response is None


def test_advisory_refusal_includes_educational_links() -> None:
    result = route_query("Should I invest in HDFC Gold ETF FoF?")
    assert result.proceed_to_rag is False
    assert result.intent == Intent.ADVISORY
    assert result.response is not None
    assert AMFI_INVESTOR_CORNER in result.response
    assert SEBI_INVESTOR_EDUCATION in result.response


def test_comparison_refusal() -> None:
    result = route_query("Which fund is better?")
    assert result.intent == Intent.COMPARISON
    assert result.proceed_to_rag is False
    assert "factual questions" in result.response.lower()


def test_performance_deflection_includes_scheme_link() -> None:
    result = route_query("What returns did HDFC Defence give last year?")
    assert result.intent == Intent.PERFORMANCE
    assert result.proceed_to_rag is False
    assert result.scheme is not None
    assert result.scheme.source_url in result.response
    assert "can't provide historical returns" in result.response.lower()


def test_performance_without_scheme_asks_for_name() -> None:
    result = route_query("What were the 3 year returns?")
    assert result.intent == Intent.PERFORMANCE
    assert result.scheme is None
    assert "name the HDFC scheme" in result.response


def test_detect_scheme_prefers_longer_alias() -> None:
    fof = detect_scheme("What is the NAV of HDFC Silver ETF FoF?")
    etf = detect_scheme("What is the NAV of HDFC Silver ETF?")
    assert fof is not None
    assert etf is not None
    assert fof.scheme_name == "HDFC Silver ETF FoF Direct Growth"
    assert etf.scheme_name == "HDFC Silver ETF"
