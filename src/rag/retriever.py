"""Hybrid retrieval: dense search, metadata reranking, and structured price injection."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from src.config import (
    AMBIGUITY_SCORE_GAP,
    GENERATOR_CONTEXT_CHUNKS,
    INDEX_DIR,
    RETRIEVAL_FETCH_K,
    SCHEME_BOOST,
    SECTION_PRIMARY_BOOST,
    SECTION_SECONDARY_BOOST,
    SIMILARITY_THRESHOLD,
    CorpusEntry,
    detect_scheme,
    load_price_snapshot,
)
from src.ingest.indexer import CHUNKS_FILENAME, search_index
from src.rag.classifier import ClassificationResult, Intent

logger = logging.getLogger(__name__)

METADATA_FILENAME = "metadata.json"

SECTION_QUERY_RULES: tuple[tuple[tuple[str, ...], tuple[str, ...], tuple[str, ...]], ...] = (
    (("expense ratio", "expense"), ("summary", "fundamentals"), ("about",)),
    (("exit load",), ("exit_load",), ("about",)),
    (
        ("minimum sip", "min sip", "minimum investment", "min investment", "sip amount"),
        ("min_investment",),
        ("summary", "about"),
    ),
    (("benchmark",), ("about",), ("summary",)),
    (("risk category", "riskometer", "risk level", "risk"), ("summary",), ("about",)),
)

PRICE_QUERY_KEYWORDS = (
    "nav",
    "price",
    "share price",
    "1-day",
    "1 day",
    "1d change",
)


@dataclass(frozen=True)
class RetrievalResult:
    """Output from the retriever for the generator and formatter."""

    chunks: list[dict[str, Any]]
    citation_chunk: dict[str, Any]
    structured_price: dict[str, Any] | None
    detected_scheme: CorpusEntry | None
    insufficient_context: bool
    needs_disambiguation: bool
    ingested_at: str


def _normalize_query(query: str) -> str:
    return " ".join(query.strip().split()).lower()


def _load_index_metadata(index_dir: Path = INDEX_DIR) -> dict[str, Any]:
    metadata_path = index_dir / METADATA_FILENAME
    if not metadata_path.is_file():
        return {}
    with metadata_path.open(encoding="utf-8") as handle:
        return json.load(handle)


def _infer_section_preferences(
    query: str,
    intent: Intent,
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    if intent == Intent.FACTUAL_PRICE:
        return ("summary",), ("price_change", "fundamentals")

    normalized = _normalize_query(query)
    for keywords, primary, secondary in SECTION_QUERY_RULES:
        if any(keyword in normalized for keyword in keywords):
            return primary, secondary
    return (), ()


def _section_boost(section: str, primary: tuple[str, ...], secondary: tuple[str, ...]) -> float:
    if section in primary:
        return SECTION_PRIMARY_BOOST
    if section in secondary:
        return SECTION_SECONDARY_BOOST
    return 0.0


def _should_inject_structured_price(
    query: str,
    intent: Intent,
    scheme: CorpusEntry | None,
) -> bool:
    if intent == Intent.FACTUAL_PRICE:
        return scheme is not None
    if scheme is None:
        return False
    normalized = _normalize_query(query)
    return any(keyword in normalized for keyword in PRICE_QUERY_KEYWORDS)


def _build_structured_price(snapshot: dict[str, Any]) -> dict[str, Any]:
    structured = {
        "section": "structured_price",
        "scheme_name": snapshot["scheme_name"],
        "source_url": snapshot["source_url"],
        "local_file": snapshot["local_file"],
        "product_type": snapshot.get("product_type"),
        "text": _format_structured_price_text(snapshot),
        "score": 1.0,
        "adjusted_score": 1.0,
    }
    for field in (
        "nav",
        "nav_date",
        "current_price",
        "change_1d_pct",
        "change_1d_abs",
        "expense_ratio_pct",
        "previous_close",
    ):
        if field in snapshot:
            structured[field] = snapshot[field]
    return structured


def _format_structured_price_text(snapshot: dict[str, Any]) -> str:
    lines = [f"Structured price data for {snapshot['scheme_name']} (authoritative):"]
    if "nav" in snapshot:
        lines.append(f"NAV: ₹{snapshot['nav']} as of {snapshot.get('nav_date', 'unknown')}")
    if "current_price" in snapshot:
        lines.append(f"Current price: ₹{snapshot['current_price']}")
    if "change_1d_abs" in snapshot:
        lines.append(
            f"1-day change: {snapshot['change_1d_abs']} ({snapshot.get('change_1d_pct', 'n/a')}%)"
        )
    elif "change_1d_pct" in snapshot:
        lines.append(f"1-day change: {snapshot['change_1d_pct']}%")
    if "expense_ratio_pct" in snapshot:
        lines.append(f"Expense ratio: {snapshot['expense_ratio_pct']}%")
    return "\n".join(lines)


def rerank_candidates(
    candidates: list[dict[str, Any]],
    *,
    query: str,
    classification: ClassificationResult,
) -> list[dict[str, Any]]:
    """Apply scheme and section boosts to semantic search results."""
    scheme = classification.scheme or detect_scheme(query)
    primary_sections, secondary_sections = _infer_section_preferences(query, classification.intent)
    reranked: list[dict[str, Any]] = []

    for candidate in candidates:
        adjusted = float(candidate["score"])
        section = candidate.get("section", "")
        if scheme is not None and candidate.get("local_file") == scheme.local_file:
            adjusted += SCHEME_BOOST
        adjusted += _section_boost(section, primary_sections, secondary_sections)
        section_priority = 0
        if section in primary_sections:
            section_priority = 2
        elif section in secondary_sections:
            section_priority = 1
        enriched = dict(candidate)
        enriched["adjusted_score"] = adjusted
        enriched["section_priority"] = section_priority
        reranked.append(enriched)

    reranked.sort(
        key=lambda item: (item["adjusted_score"], item["section_priority"]),
        reverse=True,
    )
    return reranked


def _load_all_chunks(index_dir: Path = INDEX_DIR) -> list[dict[str, Any]]:
    chunks_path = index_dir / CHUNKS_FILENAME
    if not chunks_path.is_file():
        return []
    with chunks_path.open(encoding="utf-8") as handle:
        return json.load(handle)


def _inject_primary_section_chunks(
    ranked: list[dict[str, Any]],
    *,
    scheme: CorpusEntry,
    primary_sections: tuple[str, ...],
    index_dir: Path,
) -> list[dict[str, Any]]:
    """Ensure at least one scheme chunk from the preferred section is available."""
    if not primary_sections:
        return ranked

    present = {
        (item.get("local_file"), item.get("section"))
        for item in ranked
    }
    anchor_score = ranked[0]["adjusted_score"] if ranked else 1.0
    injected: list[dict[str, Any]] = []

    for chunk in _load_all_chunks(index_dir):
        key = (chunk.get("local_file"), chunk.get("section"))
        if chunk.get("local_file") != scheme.local_file:
            continue
        if chunk.get("section") not in primary_sections:
            continue
        if key in present:
            continue
        enriched = dict(chunk)
        enriched["score"] = float(enriched.get("score", 0.0))
        enriched["adjusted_score"] = anchor_score + SECTION_PRIMARY_BOOST
        enriched["section_priority"] = 2
        injected.append(enriched)
        present.add(key)

    if not injected:
        return ranked

    merged = injected + ranked
    merged.sort(
        key=lambda item: (item["adjusted_score"], item.get("section_priority", 0)),
        reverse=True,
    )
    return merged


def _detect_ambiguity(
    ranked: list[dict[str, Any]],
    scheme: CorpusEntry | None,
) -> bool:
    if scheme is not None or len(ranked) < 2:
        return False
    top, second = ranked[0], ranked[1]
    if top.get("local_file") == second.get("local_file"):
        return False
    return abs(top["adjusted_score"] - second["adjusted_score"]) <= AMBIGUITY_SCORE_GAP


def retrieve(
    query: str,
    classification: ClassificationResult,
    *,
    index_dir: Path = INDEX_DIR,
) -> RetrievalResult:
    """Retrieve and rerank chunks for a factual query."""
    metadata = _load_index_metadata(index_dir)
    ingested_at = metadata.get("ingested_at", "")
    scheme = classification.scheme or detect_scheme(query)

    try:
        candidates = search_index(query, top_k=RETRIEVAL_FETCH_K, index_dir=index_dir)
    except FileNotFoundError:
        logger.error("Vector index unavailable in %s", index_dir)
        fallback = {
            "text": "",
            "source_url": "",
            "scheme_name": "",
            "section": "",
            "ingested_at": ingested_at,
        }
        return RetrievalResult(
            chunks=[],
            citation_chunk=fallback,
            structured_price=None,
            detected_scheme=scheme,
            insufficient_context=True,
            needs_disambiguation=False,
            ingested_at=ingested_at,
        )

    ranked = rerank_candidates(candidates, query=query, classification=classification)
    primary_sections, _ = _infer_section_preferences(query, classification.intent)
    if scheme is not None and primary_sections:
        ranked = _inject_primary_section_chunks(
            ranked,
            scheme=scheme,
            primary_sections=primary_sections,
            index_dir=index_dir,
        )
    filtered = [
        chunk for chunk in ranked if chunk["adjusted_score"] >= SIMILARITY_THRESHOLD
    ]

    structured_price = None
    if scheme and _should_inject_structured_price(query, classification.intent, scheme):
        snapshot = load_price_snapshot(scheme.local_file)
        if snapshot:
            structured_price = _build_structured_price(snapshot)

    needs_disambiguation = _detect_ambiguity(filtered, scheme)
    insufficient_context = not filtered and structured_price is None

    output_chunks = filtered[:GENERATOR_CONTEXT_CHUNKS]
    if structured_price is not None:
        output_chunks = [structured_price, *output_chunks]
        output_chunks = output_chunks[:GENERATOR_CONTEXT_CHUNKS]

    if structured_price is not None:
        citation_chunk = structured_price
    elif filtered:
        citation_chunk = filtered[0]
    elif ranked:
        citation_chunk = ranked[0]
    else:
        citation_chunk = {
            "text": "",
            "source_url": scheme.source_url if scheme else "",
            "scheme_name": scheme.scheme_name if scheme else "",
            "section": "",
            "ingested_at": ingested_at,
        }

    return RetrievalResult(
        chunks=output_chunks,
        citation_chunk=citation_chunk,
        structured_price=structured_price,
        detected_scheme=scheme,
        insufficient_context=insufficient_context,
        needs_disambiguation=needs_disambiguation,
        ingested_at=ingested_at,
    )
