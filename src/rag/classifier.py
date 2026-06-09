"""Query intent classification before RAG retrieval."""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum

from src.config import CorpusEntry, detect_scheme

ADVISORY_PATTERNS: tuple[re.Pattern[str], ...] = tuple(
    re.compile(pattern, re.IGNORECASE)
    for pattern in (
        r"\bshould\s+i\b",
        r"\bshould\s+we\b",
        r"\brecommend(?:ation|ed|s)?\b",
        r"\bgood\s+investment\b",
        r"\bworth\s+it\b",
        r"\bworth\s+buying\b",
        r"\binvest\s+in\b",
        r"\bsuitable\s+for\b",
        r"\bis\s+it\s+safe\b",
        r"\bignore\s+instructions\b",
        r"\bwhich\s+fund\s+should\b",
        r"\bwhat\s+fund\s+do\s+you\s+recommend\b",
        r"\bshould\s+i\s+buy\b",
        r"\bshould\s+i\s+sell\b",
    )
)

COMPARISON_PATTERNS: tuple[re.Pattern[str], ...] = tuple(
    re.compile(pattern, re.IGNORECASE)
    for pattern in (
        r"\bwhich\s+is\s+better\b",
        r"\bwhich\s+fund\s+is\s+better\b",
        r"\bcompare\b",
        r"\bcomparison\b",
        r"\bvs\.?\b",
        r"\bversus\b",
        r"\brank(?:ing)?\b",
        r"\bbetter\s+than\b",
        r"\bbest\s+fund\b",
        r"\btop\s+fund\b",
    )
)

PERFORMANCE_PATTERNS: tuple[re.Pattern[str], ...] = tuple(
    re.compile(pattern, re.IGNORECASE)
    for pattern in (
        r"\breturns?\b",
        r"\bcagr\b",
        r"\bannuali[sz]ed\b",
        r"\bperformance\s+over\b",
        r"\bperformance\s+history\b",
        r"\bhistorical\s+performance\b",
        r"\bnav\s+history\b",
        r"\blast\s+year\b",
        r"\byear\s+to\s+date\b",
        r"\bytd\b",
        r"\b\d+\s*[- ]?\s*y(?:ear|r)?\b",
        r"\b(?:1|3|5|10)\s*[- ]?\s*year\b",
        r"\b(?:1|3|5|10)\s*y(?:ear)?\s+(?:return|performance|cagr)\b",
    )
)

PRICE_PATTERNS: tuple[re.Pattern[str], ...] = tuple(
    re.compile(pattern, re.IGNORECASE)
    for pattern in (
        r"\bnav\b",
        r"\blatest\s+price\b",
        r"\bcurrent\s+price\b",
        r"\bshare\s+price\b",
        r"\btoday'?s\s+price\b",
        r"\b1\s*[- ]?\s*day\s+change\b",
        r"\b1d\s+change\b",
    )
)

FACTUAL_SIGNAL_PATTERNS: tuple[re.Pattern[str], ...] = tuple(
    re.compile(pattern, re.IGNORECASE)
    for pattern in (
        r"\bexpense\s+ratio\b",
        r"\bexit\s+load\b",
        r"\bbenchmark\b",
        r"\bmin(?:imum)?\s+(?:sip|investment)\b",
        r"\baum\b",
        r"\bfund\s+size\b",
        r"\brisk\s+level\b",
        r"\bvery\s+high\s+risk\b",
        r"\block[- ]?in\b",
        r"\bmutual\s+fund\b",
        r"\betf\b",
        r"\bstock\b",
        r"\bshow\s+me\b",
        r"\btell\s+me\s+about\b",
    )
)


class Intent(str, Enum):
    """Routing intent for a user query."""

    FACTUAL = "factual"
    FACTUAL_PRICE = "factual_price"
    ADVISORY = "advisory"
    COMPARISON = "comparison"
    PERFORMANCE = "performance"
    OUT_OF_SCOPE = "out_of_scope"


@dataclass(frozen=True)
class ClassificationResult:
    """Classifier output used by the refusal handler and RAG pipeline."""

    intent: Intent
    query: str
    scheme: CorpusEntry | None = None
    reason: str = ""

    @property
    def proceed_to_rag(self) -> bool:
        return self.intent in {Intent.FACTUAL, Intent.FACTUAL_PRICE}


def _normalize(query: str) -> str:
    return " ".join(query.strip().split()).lower()


def _matches_any(patterns: tuple[re.Pattern[str], ...], text: str) -> bool:
    return any(pattern.search(text) for pattern in patterns)


def _is_price_query(text: str) -> bool:
    if "nav history" in text:
        return False
    return _matches_any(PRICE_PATTERNS, text)


def _is_performance_query(text: str) -> bool:
    if _is_price_query(text) and not _matches_any(
        tuple(
            re.compile(pattern, re.IGNORECASE)
            for pattern in (
                r"\breturns?\b",
                r"\bcagr\b",
                r"\bannuali[sz]ed\b",
                r"\bperformance\s+over\b",
                r"\bperformance\s+history\b",
                r"\bhistorical\s+performance\b",
                r"\bnav\s+history\b",
                r"\blast\s+year\b",
                r"\byear\s+to\s+date\b",
                r"\bytd\b",
                r"\b\d+\s*[- ]?\s*y(?:ear|r)?\b",
                r"\b(?:1|3|5|10)\s*[- ]?\s*year\b",
            )
        ),
        text,
    ):
        return False
    return _matches_any(PERFORMANCE_PATTERNS, text)


def _has_in_scope_signal(text: str, scheme: CorpusEntry | None) -> bool:
    if scheme is not None:
        return True
    if "hdfc" in text:
        return True
    return _matches_any(FACTUAL_SIGNAL_PATTERNS, text) or _is_price_query(text)


def classify(query: str) -> ClassificationResult:
    """Classify a user query into a routing intent."""
    normalized = _normalize(query)
    if not normalized:
        return ClassificationResult(
            intent=Intent.OUT_OF_SCOPE,
            query=query,
            reason="empty_query",
        )

    scheme = detect_scheme(query)

    if _matches_any(ADVISORY_PATTERNS, normalized):
        return ClassificationResult(
            intent=Intent.ADVISORY,
            query=query,
            scheme=scheme,
            reason="advisory_keyword",
        )

    if _matches_any(COMPARISON_PATTERNS, normalized):
        return ClassificationResult(
            intent=Intent.COMPARISON,
            query=query,
            scheme=scheme,
            reason="comparison_keyword",
        )

    if _is_performance_query(normalized):
        return ClassificationResult(
            intent=Intent.PERFORMANCE,
            query=query,
            scheme=scheme,
            reason="performance_keyword",
        )

    if _is_price_query(normalized):
        return ClassificationResult(
            intent=Intent.FACTUAL_PRICE,
            query=query,
            scheme=scheme,
            reason="price_keyword",
        )

    if _has_in_scope_signal(normalized, scheme):
        return ClassificationResult(
            intent=Intent.FACTUAL,
            query=query,
            scheme=scheme,
            reason="in_scope_factual",
        )

    return ClassificationResult(
        intent=Intent.OUT_OF_SCOPE,
        query=query,
        scheme=scheme,
        reason="no_in_scope_signal",
    )
