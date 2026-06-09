"""Unit tests for response formatting and validation."""

from __future__ import annotations

import pytest

from src.config import CORPUS_ENTRIES
from src.rag.formatter import (
    count_sentences,
    format_from_retrieval,
    format_response,
    resolve_last_updated,
    truncate_to_sentences,
)

DEFENCE_URL = next(entry.source_url for entry in CORPUS_ENTRIES if "Defence" in entry.scheme_name)


def test_truncate_to_three_sentences() -> None:
    text = "One. Two. Three. Four. Five."
    assert truncate_to_sentences(text, max_sentences=3) == "One. Two. Three."


def test_count_sentences() -> None:
    assert count_sentences("First. Second! Third?") == 3


def test_format_response_includes_source_and_footer() -> None:
    output = format_response(
        "The expense ratio is 0.83%.",
        citation_url=DEFENCE_URL,
        last_updated="05 Jun 2026",
    )
    assert "Source: " + DEFENCE_URL in output
    assert "Last updated from sources: 05 Jun 2026" in output
    assert count_sentences(output.split("Source:")[0].strip()) <= 3


def test_format_rejects_non_whitelisted_url() -> None:
    with pytest.raises(ValueError):
        format_response("Answer.", citation_url="https://example.com", last_updated="05 Jun 2026")


def test_resolve_last_updated_prefers_nav_date() -> None:
    assert (
        resolve_last_updated({"nav_date": "2026-06-05"}, "2026-06-08T07:27:03+00:00")
        == "05 Jun 2026"
    )


def test_format_from_retrieval_uses_citation_chunk() -> None:
    chunk = {
        "source_url": DEFENCE_URL,
        "nav_date": "2026-06-05",
    }
    output = format_from_retrieval("The NAV is ₹28.72.", chunk, "2026-06-08T07:27:03+00:00")
    assert DEFENCE_URL in output
    assert "05 Jun 2026" in output
