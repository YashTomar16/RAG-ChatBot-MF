"""Response compliance validation for Phase 7 hardening."""

from __future__ import annotations

import re
from dataclasses import dataclass

from src.app.parse import parse_response
from src.config import is_whitelisted_url
from src.rag.formatter import count_sentences

PERFORMANCE_COMPUTED_PATTERNS = (
    re.compile(r"\b\d+\.?\d*\s*%\s*(cagr|return|annualised|annualized)", re.I),
    re.compile(r"\b(cagr|annualised return|annualized return)\s*(of|is|:)\s*\d", re.I),
)


@dataclass(frozen=True)
class ComplianceResult:
    """Outcome of validating a pipeline or API response."""

    ok: bool
    errors: tuple[str, ...]


def validate_factual_response(text: str, *, max_sentences: int = 3) -> ComplianceResult:
    """Check citation, footer, sentence limit, and whitelist for factual answers."""
    errors: list[str] = []
    parsed = parse_response(text)

    if parsed.is_refusal:
        errors.append("expected factual response but got refusal markers")

    if not parsed.source_url:
        errors.append("missing Source URL")
    elif not is_whitelisted_url(parsed.source_url):
        errors.append(f"non-whitelisted citation: {parsed.source_url}")

    if text.count("Source:") != 1:
        errors.append("response must contain exactly one Source line")

    if not parsed.last_updated:
        errors.append("missing Last updated from sources footer")

    if count_sentences(parsed.body) > max_sentences:
        errors.append(f"answer body exceeds {max_sentences} sentences")

    return ComplianceResult(ok=not errors, errors=tuple(errors))


def validate_refusal_response(text: str) -> ComplianceResult:
    """Check advisory/comparison/out-of-scope refusals include educational guidance."""
    errors: list[str] = []
    lowered = text.lower()

    if "factual questions" not in lowered and "can only help" not in lowered:
        errors.append("missing facts-only limitation statement")

    has_educational = (
        "amfiindia.com" in lowered
        or "investor.sebi.gov.in" in lowered
        or "groww.in" in lowered
    )
    if not has_educational:
        errors.append("missing educational or official link")

    if "Source:" in text:
        errors.append("refusal should not include RAG corpus citation block")

    return ComplianceResult(ok=not errors, errors=tuple(errors))


def validate_performance_deflection(text: str) -> ComplianceResult:
    """Performance queries must deflect with a link and no computed figures."""
    errors: list[str] = []
    lowered = text.lower()

    if "historical returns" not in lowered and "performance calculations" not in lowered:
        errors.append("missing performance deflection language")

    if "groww.in" not in lowered:
        errors.append("missing Groww scheme link")

    for pattern in PERFORMANCE_COMPUTED_PATTERNS:
        if pattern.search(text):
            errors.append("response appears to contain computed performance figures")
            break

    if "Source:" in text and "Last updated from sources:" in text:
        errors.append("performance deflection should not use RAG citation footer format")

    return ComplianceResult(ok=not errors, errors=tuple(errors))
