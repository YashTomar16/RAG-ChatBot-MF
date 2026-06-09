"""Phase 7 compliance validation unit tests."""

from __future__ import annotations

from src.config import CORPUS_ENTRIES
from src.validation.compliance import (
    validate_factual_response,
    validate_performance_deflection,
    validate_refusal_response,
)

DEFENCE_URL = next(entry.source_url for entry in CORPUS_ENTRIES if "Defence" in entry.scheme_name)


def test_validate_factual_response_passes_well_formed_answer() -> None:
    text = (
        "The expense ratio is 0.83%.\n\n"
        f"Source: {DEFENCE_URL}\n\n"
        "Last updated from sources: 05 Jun 2026"
    )
    result = validate_factual_response(text)
    assert result.ok, result.errors


def test_validate_factual_response_rejects_missing_citation() -> None:
    result = validate_factual_response("The expense ratio is 0.83%.")
    assert not result.ok
    assert any("Source" in error for error in result.errors)


def test_validate_factual_response_rejects_non_whitelisted_url() -> None:
    text = (
        "Answer.\n\nSource: https://example.com/bad\n\nLast updated from sources: 05 Jun 2026"
    )
    result = validate_factual_response(text)
    assert not result.ok
    assert any("whitelist" in error for error in result.errors)


def test_validate_factual_response_rejects_long_answer() -> None:
    text = (
        "One. Two. Three. Four.\n\n"
        f"Source: {DEFENCE_URL}\n\n"
        "Last updated from sources: 05 Jun 2026"
    )
    result = validate_factual_response(text)
    assert not result.ok
    assert any("sentences" in error for error in result.errors)


def test_validate_refusal_includes_educational_links() -> None:
    text = (
        "I understand you're looking for guidance. "
        "I can only answer factual questions about HDFC schemes from official Groww pages.\n\n"
        "For general mutual fund education, visit: https://www.amfiindia.com/investor-corner"
    )
    result = validate_refusal_response(text)
    assert result.ok, result.errors


def test_validate_refusal_rejects_rag_citation_block() -> None:
    text = (
        "I can only answer factual questions.\n\n"
        f"Source: {DEFENCE_URL}\n\n"
        "Last updated from sources: 05 Jun 2026"
    )
    result = validate_refusal_response(text)
    assert not result.ok


def test_validate_performance_deflection() -> None:
    text = (
        "I can't provide historical returns or performance calculations. "
        f"View the official Groww page:\n\n{DEFENCE_URL}"
    )
    result = validate_performance_deflection(text)
    assert result.ok, result.errors


def test_validate_performance_rejects_computed_cagr() -> None:
    text = (
        "The 3Y CAGR is 15.2% for this fund. "
        f"See {DEFENCE_URL}"
    )
    result = validate_performance_deflection(text)
    assert not result.ok
