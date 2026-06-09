"""Shared helpers for API and legacy Streamlit UI."""

from __future__ import annotations

from typing import Any

from src.app.data import (
    MOCK_ALLOCATION,
    MOCK_GOAL,
    MOCK_PORTFOLIO,
    PRODUCT_TYPE_LABELS,
    format_change,
    format_price,
)


def serialize_product(product: dict[str, Any]) -> dict[str, Any]:
    """Enrich a price snapshot row with display fields for clients."""
    change_text, change_direction = format_change(product)
    aum = product.get("aum_cr")
    market_cap = product.get("market_cap_cr")
    return {
        **product,
        "product_type_label": PRODUCT_TYPE_LABELS.get(
            product.get("product_type", ""), product.get("product_type", "")
        ),
        "price_display": format_price(product),
        "change_display": change_text,
        "change_direction": change_direction,
        "aum_display": f"₹{aum:,.0f} Cr" if aum is not None else None,
        "market_cap_display": f"₹{market_cap:,.0f} Cr" if market_cap is not None else None,
    }


def mock_portfolio_payload() -> dict[str, Any]:
    gain = MOCK_PORTFOLIO["value"] - MOCK_PORTFOLIO["invested"]
    return {
        **MOCK_PORTFOLIO,
        "gain": gain,
        "gain_positive": gain >= 0,
    }


def mock_goal_payload() -> dict[str, Any]:
    progress = min(100, int(MOCK_GOAL["current"] / MOCK_GOAL["target"] * 100))
    return {**MOCK_GOAL, "progress_pct": progress}


def mock_allocation_payload() -> list[dict[str, Any]]:
    return [
        {"label": label, "pct": pct, "color": color}
        for label, pct, color in MOCK_ALLOCATION
    ]


SUGGESTED_PROMPTS = [
    "What is the expense ratio of HDFC Defence Fund Direct Growth?",
    "What is the minimum SIP for HDFC Gold ETF FoF?",
    "What is the exit load on HDFC Silver ETF FoF Direct Growth?",
    "What is the latest NAV of HDFC Defence Fund Direct Growth?",
    "What is the risk category of HDFC Balanced Advantage Fund?",
    "What is the 1-day change for HDFC Silver ETF?",
]
