"""Unit tests for UI response parsing and data helpers."""

from __future__ import annotations

from src.app.data import format_change, format_price, search_products
from src.app.parse import is_refusal_response, parse_response


def test_parse_factual_response() -> None:
    raw = (
        "The expense ratio is 0.83%.\n\n"
        "Source: https://groww.in/mutual-funds/hdfc-defence-fund-direct-growth\n\n"
        "Last updated from sources: 05 Jun 2026"
    )
    parsed = parse_response(raw)
    assert parsed.body == "The expense ratio is 0.83%."
    assert "hdfc-defence-fund" in (parsed.source_url or "")
    assert parsed.last_updated == "05 Jun 2026"
    assert not parsed.is_refusal


def test_parse_refusal_response() -> None:
    raw = (
        "I understand you're looking for guidance. "
        "I can only answer factual questions about HDFC schemes from official Groww pages.\n\n"
        "For general mutual fund education, visit: https://www.amfiindia.com/investor-corner"
    )
    parsed = parse_response(raw)
    assert parsed.is_refusal
    assert is_refusal_response(raw)


def test_format_price_mutual_fund() -> None:
    product = {"nav": 28.72, "product_type": "mutual_fund"}
    assert format_price(product) == "₹28.72"


def test_format_change_gain_uses_gain_class() -> None:
    text, css_class = format_change({"change_1d_pct": 0.18})
    assert text == "+0.18%"
    assert css_class == "gain"


def test_format_change_loss() -> None:
    text, css_class = format_change({"change_1d_pct": -1.28})
    assert text == "-1.28%"
    assert css_class == "loss"


def test_search_products_by_name() -> None:
    results = search_products("defence")
    assert len(results) >= 1
    assert any("Defence" in r["scheme_name"] for r in results)
