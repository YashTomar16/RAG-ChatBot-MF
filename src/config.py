"""Application configuration, corpus URL registry, and path constants."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv

ProductType = Literal["mutual_fund", "etf", "stock"]

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CORPUS_DIR = PROJECT_ROOT / "data" / "corpus" / "groww"
PRICE_SNAPSHOTS_PATH = PROJECT_ROOT / "data" / "corpus" / "price_snapshots.json"
PRICE_SNAPSHOTS_SCHEMA_PATH = (
    PROJECT_ROOT / "data" / "corpus" / "price_snapshots.schema.json"
)
INDEX_DIR = PROJECT_ROOT / "index"
INGESTION_LOG_PATH = PROJECT_ROOT / "data" / "ingestion_log.json"

load_dotenv(PROJECT_ROOT / ".env")

TIMEZONE = os.getenv("TIMEZONE", "Asia/Kolkata")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
EMBEDDING_PROVIDER = os.getenv("EMBEDDING_PROVIDER", "bge").lower()
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "auto")
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "groq").lower()
LLM_MODEL = os.getenv("LLM_MODEL", "llama-3.3-70b-versatile")
TOP_K = int(os.getenv("TOP_K", "5"))
SIMILARITY_THRESHOLD = float(os.getenv("SIMILARITY_THRESHOLD", "0.7"))
RETRIEVAL_FETCH_K = int(os.getenv("RETRIEVAL_FETCH_K", "8"))
GENERATOR_CONTEXT_CHUNKS = int(os.getenv("GENERATOR_CONTEXT_CHUNKS", "3"))
SCHEME_BOOST = float(os.getenv("SCHEME_BOOST", "0.15"))
SECTION_PRIMARY_BOOST = float(os.getenv("SECTION_PRIMARY_BOOST", "0.10"))
SECTION_SECONDARY_BOOST = float(os.getenv("SECTION_SECONDARY_BOOST", "0.05"))
AMBIGUITY_SCORE_GAP = float(os.getenv("AMBIGUITY_SCORE_GAP", "0.05"))


@dataclass(frozen=True)
class CorpusEntry:
    """Single Groww page in the curated corpus."""

    id: int
    scheme_name: str
    product_type: ProductType
    source_url: str
    local_file: str


# Single source of truth for the 12 Groww URLs and local file mappings.
CORPUS_ENTRIES: tuple[CorpusEntry, ...] = (
    CorpusEntry(
        id=1,
        scheme_name="HDFC Silver ETF FoF Direct Growth",
        product_type="mutual_fund",
        source_url="https://groww.in/mutual-funds/hdfc-silver-etf-fof-direct-growth",
        local_file="hdfc-silver-etf-fof-direct-growth.md",
    ),
    CorpusEntry(
        id=2,
        scheme_name="HDFC Mid Cap Fund Direct Growth",
        product_type="mutual_fund",
        source_url="https://groww.in/mutual-funds/hdfc-mid-cap-fund-direct-growth",
        local_file="hdfc-mid-cap-fund-direct-growth-2.md",
    ),
    CorpusEntry(
        id=3,
        scheme_name="HDFC Flexi Cap Direct Plan Growth",
        product_type="mutual_fund",
        source_url="https://groww.in/mutual-funds/hdfc-equity-fund-direct-growth",
        local_file="hdfc-equity-fund-direct-growth-3.md",
    ),
    CorpusEntry(
        id=4,
        scheme_name="HDFC Defence Fund Direct Growth",
        product_type="mutual_fund",
        source_url="https://groww.in/mutual-funds/hdfc-defence-fund-direct-growth",
        local_file="hdfc-defence-fund-direct-growth.md",
    ),
    CorpusEntry(
        id=5,
        scheme_name="HDFC Small Cap Fund Direct Growth",
        product_type="mutual_fund",
        source_url="https://groww.in/mutual-funds/hdfc-small-cap-fund-direct-growth",
        local_file="hdfc-small-cap-fund-direct-growth-7.md",
    ),
    CorpusEntry(
        id=6,
        scheme_name="HDFC Gold ETF Fund of Fund Direct Plan Growth",
        product_type="mutual_fund",
        source_url="https://groww.in/mutual-funds/hdfc-gold-etf-fund-of-fund-direct-plan-growth",
        local_file="hdfc-gold-etf-fund-of-fund-direct-plan-growth.md",
    ),
    CorpusEntry(
        id=7,
        scheme_name="HDFC Balanced Advantage Fund Direct Growth",
        product_type="mutual_fund",
        source_url="https://groww.in/mutual-funds/hdfc-balanced-advantage-fund-direct-growth",
        local_file="hdfc-balanced-advantage-fund-direct-growth-11.md",
    ),
    CorpusEntry(
        id=8,
        scheme_name="HDFC Silver ETF",
        product_type="etf",
        source_url="https://groww.in/etfs/hdfc-silver-etf",
        local_file="hdfc-silver-etf-6.md",
    ),
    CorpusEntry(
        id=9,
        scheme_name="HDFC NIFTY Smallcap 250 ETF",
        product_type="etf",
        source_url="https://groww.in/etfs/hdfc-nifty-smallcap-etf",
        local_file="hdfc-nifty-smallcap-etf-9.md",
    ),
    CorpusEntry(
        id=10,
        scheme_name="HDFC Gold ETF",
        product_type="etf",
        source_url="https://groww.in/etfs/hdfc-mutual-fundhdfc-gold-exchange-traded-fund",
        local_file="hdfc-mutual-fundhdfc-gold-exchange-traded-fund-10.md",
    ),
    CorpusEntry(
        id=11,
        scheme_name="HDFC Bank Ltd",
        product_type="stock",
        source_url="https://groww.in/stocks/hdfc-bank-ltd",
        local_file="hdfc-bank-ltd-1.md",
    ),
    CorpusEntry(
        id=12,
        scheme_name="HDFC Life Insurance Company Ltd",
        product_type="stock",
        source_url="https://groww.in/stocks/hdfc-standard-life-insurance-co-ltd",
        local_file="hdfc-standard-life-insurance-co-ltd-5.md",
    ),
)

CORPUS_URL_WHITELIST: frozenset[str] = frozenset(
    entry.source_url for entry in CORPUS_ENTRIES
)

CORPUS_BY_URL: dict[str, CorpusEntry] = {
    entry.source_url: entry for entry in CORPUS_ENTRIES
}

CORPUS_BY_LOCAL_FILE: dict[str, CorpusEntry] = {
    entry.local_file: entry for entry in CORPUS_ENTRIES
}

# Common aliases for scheme detection and URL lookup (longest match wins).
SCHEME_ALIASES: dict[str, tuple[str, ...]] = {
    "HDFC Defence Fund Direct Growth": ("hdfc defence", "defence fund"),
    "HDFC Mid Cap Fund Direct Growth": ("hdfc mid cap", "mid cap fund"),
    "HDFC Flexi Cap Direct Plan Growth": (
        "hdfc flexi cap",
        "hdfc equity fund",
        "flexi cap",
    ),
    "HDFC Small Cap Fund Direct Growth": ("hdfc small cap", "small cap fund"),
    "HDFC Gold ETF Fund of Fund Direct Plan Growth": (
        "hdfc gold etf fof",
        "gold etf fof",
        "hdfc gold etf fund of fund",
        "gold etf fund of fund",
    ),
    "HDFC Silver ETF FoF Direct Growth": (
        "hdfc silver etf fof",
        "silver etf fof",
        "hdfc silver etf fund of fund",
        "silver etf fund of fund",
    ),
    "HDFC Balanced Advantage Fund Direct Growth": (
        "hdfc balanced advantage",
        "balanced advantage",
    ),
    "HDFC Silver ETF": ("hdfc silver etf",),
    "HDFC NIFTY Smallcap 250 ETF": (
        "hdfc nifty smallcap",
        "smallcap 250 etf",
    ),
    "HDFC Gold ETF": ("hdfc gold etf",),
    "HDFC Bank Ltd": ("hdfc bank",),
    "HDFC Life Insurance Company Ltd": ("hdfc life", "hdfc life insurance"),
}


def _scheme_match_candidates() -> list[tuple[str, CorpusEntry]]:
    candidates: list[tuple[str, CorpusEntry]] = []
    for entry in CORPUS_ENTRIES:
        candidates.append((entry.scheme_name.lower(), entry))
        for alias in SCHEME_ALIASES.get(entry.scheme_name, ()):
            candidates.append((alias.lower(), entry))
    candidates.sort(key=lambda item: len(item[0]), reverse=True)
    return candidates


_SCHEME_MATCH_CANDIDATES = _scheme_match_candidates()


def detect_scheme(query: str) -> CorpusEntry | None:
    """Return the best-matching corpus entry for a query, if any."""
    normalized = query.lower()
    for alias, entry in _SCHEME_MATCH_CANDIDATES:
        if alias in normalized:
            return entry
    return None


def build_scheme_url_lookup() -> dict[str, str]:
    """Map scheme names and aliases to Groww URLs."""
    lookup: dict[str, str] = {}
    for entry in CORPUS_ENTRIES:
        lookup[entry.scheme_name.lower()] = entry.source_url
        for alias in SCHEME_ALIASES.get(entry.scheme_name, ()):
            lookup[alias.lower()] = entry.source_url
    return lookup


def corpus_file_path(entry: CorpusEntry) -> Path:
    """Return absolute path to a corpus markdown file."""
    return CORPUS_DIR / entry.local_file


def is_whitelisted_url(url: str) -> bool:
    """Check whether a URL is in the 12-link citation whitelist."""
    return url in CORPUS_URL_WHITELIST


def all_corpus_files_exist() -> bool:
    """Return True if every expected corpus markdown file is present."""
    return all(corpus_file_path(entry).is_file() for entry in CORPUS_ENTRIES)


def load_price_snapshot(local_file: str) -> dict | None:
    """Return the price snapshot row for a corpus file, if present."""
    if not PRICE_SNAPSHOTS_PATH.is_file():
        return None
    import json

    with PRICE_SNAPSHOTS_PATH.open(encoding="utf-8") as handle:
        payload = json.load(handle)
    for product in payload.get("products", []):
        if product.get("local_file") == local_file:
            return product
    return None
