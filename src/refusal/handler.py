"""Advisory, comparison, performance deflection, and out-of-scope responses."""

from __future__ import annotations

from dataclasses import dataclass

from src.config import CorpusEntry
from src.rag.classifier import ClassificationResult, Intent, classify

AMFI_INVESTOR_CORNER = "https://www.amfiindia.com/investor-corner"
SEBI_INVESTOR_EDUCATION = "https://investor.sebi.gov.in"
GROWW_MUTUAL_FUNDS = "https://groww.in/mutual-funds"

REFUSAL_BODY = (
    "I can only answer factual questions about HDFC schemes from official Groww pages."
)


@dataclass(frozen=True)
class RouteResult:
    """Outcome of routing a query before the RAG pipeline."""

    intent: Intent
    response: str | None
    proceed_to_rag: bool
    scheme: CorpusEntry | None = None


def _refusal_response() -> str:
    return (
        "I understand you're looking for guidance. "
        f"{REFUSAL_BODY}\n\n"
        f"For general mutual fund education, visit: {AMFI_INVESTOR_CORNER}\n"
        f"For investor awareness, visit: {SEBI_INVESTOR_EDUCATION}"
    )


def _performance_response(scheme: CorpusEntry | None) -> str:
    if scheme is not None:
        return (
            "I can't provide historical returns or performance calculations. "
            f"For return charts and performance data, view the official Groww page:\n\n"
            f"{scheme.source_url}"
        )

    return (
        "I can't provide historical returns or performance calculations. "
        "Please name the HDFC scheme you'd like to view "
        f"(for example, HDFC Defence Fund Direct Growth), or browse funds on Groww:\n\n"
        f"{GROWW_MUTUAL_FUNDS}"
    )


def _out_of_scope_response() -> str:
    return (
        "I can only help with factual questions about HDFC schemes from our Groww corpus. "
        "Please ask about expense ratios, NAV, exit load, benchmarks, or similar facts "
        "for one of the supported HDFC mutual funds, ETFs, or related stocks."
    )


def build_response(result: ClassificationResult) -> str:
    """Build a user-facing response for non-RAG intents."""
    if result.intent in {Intent.ADVISORY, Intent.COMPARISON}:
        return _refusal_response()
    if result.intent == Intent.PERFORMANCE:
        return _performance_response(result.scheme)
    if result.intent == Intent.OUT_OF_SCOPE:
        return _out_of_scope_response()
    raise ValueError(f"No refusal response for intent: {result.intent}")


def route_query(query: str) -> RouteResult:
    """Classify a query and return either a refusal response or a RAG proceed signal."""
    result = classify(query)
    if result.proceed_to_rag:
        return RouteResult(
            intent=result.intent,
            response=None,
            proceed_to_rag=True,
            scheme=result.scheme,
        )

    return RouteResult(
        intent=result.intent,
        response=build_response(result),
        proceed_to_rag=False,
        scheme=result.scheme,
    )
