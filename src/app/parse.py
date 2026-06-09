"""Parse pipeline responses for UI rendering."""

from __future__ import annotations

import re
from dataclasses import dataclass

REFUSAL_MARKERS = (
    "amfiindia.com",
    "investor.sebi.gov.in",
    "i understand you're looking for guidance",
    "i can't provide historical returns",
    "i can only help with factual questions",
)

SOURCE_PATTERN = re.compile(r"^Source:\s*(https?://\S+)\s*$", re.MULTILINE)
FOOTER_PATTERN = re.compile(
    r"^Last updated from sources:\s*(.+?)\s*$",
    re.MULTILINE,
)


@dataclass(frozen=True)
class ParsedResponse:
    """Structured assistant response for the chat UI."""

    body: str
    source_url: str | None
    last_updated: str | None
    is_refusal: bool
    is_performance_deflection: bool
    raw: str


def is_refusal_response(text: str) -> bool:
    """Detect advisory, comparison, or out-of-scope refusals."""
    lowered = text.lower()
    return any(marker in lowered for marker in REFUSAL_MARKERS)


def is_performance_deflection(text: str) -> bool:
    """Detect performance deflection (Groww link only, no RAG answer)."""
    lowered = text.lower()
    return "historical returns" in lowered or "performance calculations" in lowered


def parse_response(text: str) -> ParsedResponse:
    """Split a pipeline response into body, citation, and footer."""
    source_match = SOURCE_PATTERN.search(text)
    footer_match = FOOTER_PATTERN.search(text)

    source_url = source_match.group(1) if source_match else None
    last_updated = footer_match.group(1) if footer_match else None

    body = text
    if source_match:
        body = text[: source_match.start()].strip()
    elif footer_match:
        body = text[: footer_match.start()].strip()

    return ParsedResponse(
        body=body,
        source_url=source_url,
        last_updated=last_updated,
        is_refusal=is_refusal_response(text),
        is_performance_deflection=is_performance_deflection(text),
        raw=text,
    )
