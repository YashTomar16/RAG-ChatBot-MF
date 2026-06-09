"""Load corpus and price snapshot data for the UI."""

from __future__ import annotations

import json
from typing import Any

from src.config import CORPUS_ENTRIES, PRICE_SNAPSHOTS_PATH, CorpusEntry, detect_scheme

PRODUCT_TYPE_LABELS = {
    "mutual_fund": "Mutual Fund",
    "etf": "ETF",
    "stock": "Stock",
}


def load_price_snapshots() -> dict[str, Any]:
    """Load the full price snapshots payload (always read from disk — refreshed by scheduler)."""
    if not PRICE_SNAPSHOTS_PATH.is_file():
        return {"products": [], "as_of_date": None}
    with PRICE_SNAPSHOTS_PATH.open(encoding="utf-8") as handle:
        return json.load(handle)


def all_products() -> list[dict[str, Any]]:
    """Return all product rows from price snapshots."""
    return list(load_price_snapshots().get("products", []))


def product_by_id(product_id: int) -> dict[str, Any] | None:
    """Look up a product by corpus id."""
    for product in all_products():
        if product.get("id") == product_id:
            return product
    return None


def product_for_entry(entry: CorpusEntry) -> dict[str, Any] | None:
    """Return price snapshot row for a corpus entry."""
    return product_by_id(entry.id)


def entry_by_id(entry_id: int) -> CorpusEntry | None:
    """Return corpus entry by id."""
    for entry in CORPUS_ENTRIES:
        if entry.id == entry_id:
            return entry
    return None


def detect_product_from_text(text: str) -> dict[str, Any] | None:
    """Match query text to a price snapshot product."""
    entry = detect_scheme(text)
    if entry is None:
        return None
    return product_for_entry(entry)


def format_price(product: dict[str, Any]) -> str:
    """Format NAV or share price for display."""
    if product.get("nav") is not None:
        return f"₹{product['nav']:,.2f}"
    if product.get("current_price") is not None:
        return f"₹{product['current_price']:,.2f}"
    return "—"


def format_change(product: dict[str, Any]) -> tuple[str, str]:
    """Return (display text, css class) for 1D change. Green only for gains."""
    pct = product.get("change_1d_pct")
    if pct is None:
        return "—", "neutral"
    sign = "+" if pct > 0 else ""
    text = f"{sign}{pct:.2f}%"
    if pct > 0:
        return text, "gain"
    if pct < 0:
        return text, "loss"
    return text, "neutral"


def search_products(query: str) -> list[dict[str, Any]]:
    """Filter products by scheme name or product type."""
    normalized = query.strip().lower()
    if not normalized:
        return all_products()
    results: list[dict[str, Any]] = []
    for product in all_products():
        name = product.get("scheme_name", "").lower()
        ptype = product.get("product_type", "").lower()
        label = PRODUCT_TYPE_LABELS.get(ptype, ptype).lower()
        if normalized in name or normalized in ptype or normalized in label:
            results.append(product)
    return results


MOCK_PORTFOLIO = {
    "value": 842_350.0,
    "invested": 750_000.0,
    "xirr": 14.2,
    "period": "1Y",
}

MOCK_GOAL = {
    "name": "Retirement corpus",
    "target": 2_000_000.0,
    "current": 842_350.0,
    "deadline": "2045",
}

MOCK_ALLOCATION = [
    ("Equity", 55, "#5367F5"),
    ("Debt", 25, "#6B7280"),
    ("Gold", 12, "#FFB300"),
    ("Cash", 8, "#98989D"),
]
