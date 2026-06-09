"""Citation and footer enforcement on LLM output."""

from __future__ import annotations

import re
from datetime import datetime
from typing import Any

from src.config import is_whitelisted_url

_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+")
_ISO_DATE = re.compile(r"^(\d{4})-(\d{2})-(\d{2})$")
_MONTHS = (
    "Jan",
    "Feb",
    "Mar",
    "Apr",
    "May",
    "Jun",
    "Jul",
    "Aug",
    "Sep",
    "Oct",
    "Nov",
    "Dec",
)


def count_sentences(text: str) -> int:
    """Count sentences in answer text."""
    cleaned = text.strip()
    if not cleaned:
        return 0
    parts = [part.strip() for part in _SENTENCE_SPLIT.split(cleaned) if part.strip()]
    return len(parts)


def truncate_to_sentences(text: str, max_sentences: int = 3) -> str:
    """Keep only the first N sentences from answer text."""
    cleaned = text.strip()
    if not cleaned:
        return cleaned
    parts = [part.strip() for part in _SENTENCE_SPLIT.split(cleaned) if part.strip()]
    if len(parts) <= max_sentences:
        return cleaned
    return " ".join(parts[:max_sentences]).strip()


def _format_display_date(value: str) -> str:
    if not value:
        return "unknown date"
    date_part = value[:10]
    match = _ISO_DATE.match(date_part)
    if match:
        year, month, day = match.groups()
        month_index = int(month)
        if 1 <= month_index <= 12:
            return f"{int(day):02d} {_MONTHS[month_index - 1]} {year}"
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return parsed.strftime("%d %b %Y")
    except ValueError:
        return date_part


def resolve_last_updated(citation_chunk: dict[str, Any], ingested_at: str) -> str:
    """Pick the best last-updated date for the response footer."""
    if citation_chunk.get("nav_date"):
        return _format_display_date(str(citation_chunk["nav_date"]))
    if citation_chunk.get("ingested_at"):
        return _format_display_date(str(citation_chunk["ingested_at"]))
    if ingested_at:
        return _format_display_date(ingested_at)
    return "unknown date"


def format_response(
    answer: str,
    *,
    citation_url: str,
    last_updated: str,
    max_sentences: int = 3,
) -> str:
    """Enforce length, inject whitelisted citation, and append footer."""
    trimmed = truncate_to_sentences(answer, max_sentences=max_sentences)
    if not trimmed:
        trimmed = "I don't have enough information to answer that question."

    if not citation_url or not is_whitelisted_url(citation_url):
        raise ValueError(f"Citation URL is missing or not whitelisted: {citation_url!r}")

    return (
        f"{trimmed}\n\n"
        f"Source: {citation_url}\n\n"
        f"Last updated from sources: {last_updated}"
    )


def format_from_retrieval(
    answer: str,
    citation_chunk: dict[str, Any],
    ingested_at: str,
) -> str:
    """Format an LLM answer using retrieval citation metadata."""
    citation_url = citation_chunk.get("source_url", "")
    last_updated = resolve_last_updated(citation_chunk, ingested_at)
    return format_response(
        answer,
        citation_url=citation_url,
        last_updated=last_updated,
    )
