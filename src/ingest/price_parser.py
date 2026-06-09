"""Extract NAV, share price, 1-day change, and scheme facts from Groww corpus markdown."""

from __future__ import annotations

import json
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from bs4 import BeautifulSoup

from src.config import (
    CORPUS_ENTRIES,
    PRICE_SNAPSHOTS_PATH,
    CorpusEntry,
    ProductType,
)

logger = logging.getLogger(__name__)

_MONTH_MAP = {
    "Jan": 1,
    "Feb": 2,
    "Mar": 3,
    "Apr": 4,
    "May": 5,
    "Jun": 6,
    "Jul": 7,
    "Aug": 8,
    "Sep": 9,
    "Oct": 10,
    "Nov": 11,
    "Dec": 12,
}


def _normalize_text(text: str) -> str:
    """Normalize markdown escapes and whitespace for regex parsing."""
    text = text.replace("\\-", "-")
    text = text.replace("\\", "")
    return text


def _parse_indian_number(value: str) -> float:
    """Parse numbers like 9,123.61 or 11,50,743."""
    return float(value.replace(",", ""))


def _parse_nav_date(raw_date: str) -> str:
    """Convert Groww NAV date (e.g. 05 Jun '26) to ISO format."""
    match = re.match(r"(\d{2})\s+(\w{3})\s+'(\d{2})", raw_date.strip())
    if not match:
        raise ValueError(f"Unrecognized NAV date format: {raw_date!r}")

    day, month_abbr, year_suffix = match.groups()
    month = _MONTH_MAP.get(month_abbr)
    if month is None:
        raise ValueError(f"Unrecognized month in NAV date: {raw_date!r}")

    year = 2000 + int(year_suffix)
    return datetime(year, month, int(day)).date().isoformat()


def _next_value_after_label(text: str, label: str) -> str | None:
    """Return the first non-empty line after a label."""
    pattern = rf"{re.escape(label)}\s*\n+\s*([^\n]+)"
    match = re.search(pattern, text, flags=re.IGNORECASE)
    return match.group(1).strip() if match else None


def _parse_expense_ratio_pct(text: str) -> float | None:
    """Parse expense ratio from the first summary 'Expense ratio' block."""
    line = _next_value_after_label(text, "Expense ratio")
    if not line:
        return None
    match = re.match(r"([\d.]+)\s*%", line.strip())
    if match:
        return float(match.group(1))
    return None


def parse_mutual_fund_prices(markdown: str) -> dict[str, Any]:
    """Parse mutual fund NAV, 1D change, and AUM from markdown body."""
    text = _normalize_text(markdown)
    result: dict[str, Any] = {}

    change_match = re.search(r"([+-]?[\d.]+)%\s*1D", text)
    if change_match:
        result["change_1d_pct"] = float(change_match.group(1))

    nav_date_match = re.search(r"NAV:\s*([^\n]+)", text)
    if nav_date_match:
        result["nav_date"] = _parse_nav_date(nav_date_match.group(1))

    nav_match = re.search(r"NAV:\s*[^\n]+\n+\s*₹([\d,]+\.?\d*)", text)
    if nav_match:
        result["nav"] = _parse_indian_number(nav_match.group(1))

    aum_line = _next_value_after_label(text, "Fund size (AUM)")
    if aum_line:
        aum_match = re.search(r"₹([\d,]+\.?\d*)\s*Cr", aum_line)
        if aum_match:
            result["aum_cr"] = _parse_indian_number(aum_match.group(1))

    expense_ratio = _parse_expense_ratio_pct(text)
    if expense_ratio is not None:
        result["expense_ratio_pct"] = expense_ratio

    return result


def parse_traded_product_prices(markdown: str, product_type: ProductType) -> dict[str, Any]:
    """Parse ETF or stock price, 1D change, and market metrics from markdown body."""
    text = _normalize_text(markdown)
    result: dict[str, Any] = {}

    price_match = re.search(
        r"₹([\d,]+\.\d{2})([+-]?[\d.]+)?\s*\(([+-]?[\d.]+)%\)\s*1D",
        text,
    )
    if price_match:
        result["current_price"] = _parse_indian_number(price_match.group(1))
        change_abs_raw = price_match.group(2)
        pct_raw = price_match.group(3)

        if change_abs_raw:
            result["change_1d_abs"] = float(change_abs_raw)
        elif pct_raw:
            # Positive moves sometimes omit the explicit sign on the absolute change.
            result["change_1d_abs"] = abs(float(pct_raw))

        pct = float(pct_raw) if pct_raw else 0.0
        if pct_raw and "+" not in pct_raw and "-" not in pct_raw:
            abs_change = result.get("change_1d_abs", 0.0)
            if abs_change < 0:
                pct = -abs(pct)
            elif abs_change > 0:
                pct = abs(pct)
        result["change_1d_pct"] = pct

    previous_close_line = _next_value_after_label(text, "Previous close")
    if previous_close_line:
        prev_match = re.search(r"([\d,]+\.?\d*)", previous_close_line)
        if prev_match:
            result["previous_close"] = _parse_indian_number(prev_match.group(1))

    if product_type == "etf":
        expense_ratio = _parse_expense_ratio_pct(text)
        if expense_ratio is not None:
            result["expense_ratio_pct"] = expense_ratio

        aum_line = _next_value_after_label(text, "AUM")
        if aum_line:
            aum_match = re.search(r"₹([\d,]+)\s*Cr", aum_line)
            if aum_match:
                result["market_cap_cr"] = _parse_indian_number(aum_match.group(1))
    elif product_type == "stock":
        market_cap_line = _next_value_after_label(text, "Market Cap")
        if market_cap_line:
            cap_match = re.search(r"₹([\d,]+)\s*Cr", market_cap_line, flags=re.IGNORECASE)
            if cap_match:
                result["market_cap_cr"] = _parse_indian_number(cap_match.group(1))

    return result


def parse_prices_from_markdown(entry: CorpusEntry, markdown: str) -> dict[str, Any]:
    """Parse pricing fields for a corpus entry from markdown content."""
    body = _strip_canonical_header(markdown)
    if entry.product_type == "mutual_fund":
        return parse_mutual_fund_prices(body)
    return parse_traded_product_prices(body, entry.product_type)


def parse_prices_from_html(entry: CorpusEntry, html: str) -> dict[str, Any]:
    """Parse pricing fields from raw HTML, falling back to converted markdown."""
    soup = BeautifulSoup(html, "html.parser")
    markdown = soup.get_text("\n", strip=True)
    return parse_prices_from_markdown(entry, markdown)


def _strip_canonical_header(markdown: str) -> str:
    """Remove Source URL / Title header block from markdown."""
    lines = markdown.splitlines()
    if len(lines) >= 2 and lines[0].startswith("Source URL:") and lines[1].startswith("Title:"):
        for index, line in enumerate(lines[2:], start=2):
            if line.strip():
                return "\n".join(lines[index:])
        return ""
    return markdown


def _product_base(entry: CorpusEntry) -> dict[str, Any]:
    return {
        "id": entry.id,
        "scheme_name": entry.scheme_name,
        "product_type": entry.product_type,
        "source_url": entry.source_url,
        "local_file": entry.local_file,
    }


def build_product_snapshot(
    entry: CorpusEntry,
    parsed: dict[str, Any],
    previous: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Merge parsed pricing fields into a product snapshot record."""
    product = _product_base(entry)
    if previous:
        product.update({k: v for k, v in previous.items() if k not in product})

    product.update(parsed)
    return product


def _validate_product(product: dict[str, Any]) -> None:
    product_type = product["product_type"]
    if product_type == "mutual_fund":
        required = ("nav", "nav_date", "change_1d_pct")
    else:
        required = ("current_price", "change_1d_pct")
    missing = [field for field in required if field not in product]
    if missing:
        raise ValueError(f"Missing required fields {missing} for {product['scheme_name']}")


def load_existing_snapshots(path: Path = PRICE_SNAPSHOTS_PATH) -> dict[str, Any]:
    """Load the current price snapshot file, or return an empty scaffold."""
    if not path.is_file():
        return {
            "schema_version": "1.0",
            "description": (
                "Point-in-time NAV, share price, and 1-day change extracted from Groww pages. "
                "Refreshed on each scheduled ingestion run."
            ),
            "as_of_date": datetime.now().date().isoformat(),
            "currency": "INR",
            "products": [],
        }

    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def update_price_snapshots(
    parsed_by_id: dict[int, dict[str, Any]],
    path: Path = PRICE_SNAPSHOTS_PATH,
) -> dict[str, Any]:
    """Atomically update price_snapshots.json with newly parsed product data."""
    existing = load_existing_snapshots(path)
    previous_by_id = {product["id"]: product for product in existing.get("products", [])}

    products: list[dict[str, Any]] = []
    nav_dates: list[str] = []

    for entry in CORPUS_ENTRIES:
        previous = previous_by_id.get(entry.id)
        parsed = parsed_by_id.get(entry.id)
        if parsed:
            product = build_product_snapshot(entry, parsed, previous)
            try:
                _validate_product(product)
            except ValueError as exc:
                logger.warning("Validation failed for %s: %s", entry.source_url, exc)
                if previous:
                    products.append(previous)
                continue
            products.append(product)
            if product.get("nav_date"):
                nav_dates.append(product["nav_date"])
        elif previous:
            products.append(previous)
        else:
            logger.warning("No price data available for %s", entry.source_url)

    products.sort(key=lambda item: item["id"])
    as_of_date = max(nav_dates) if nav_dates else existing.get("as_of_date", datetime.now().date().isoformat())

    snapshot = {
        "schema_version": "1.0",
        "description": existing.get(
            "description",
            "Point-in-time NAV, share price, and 1-day change extracted from Groww pages. "
            "Refreshed on each scheduled ingestion run.",
        ),
        "as_of_date": as_of_date,
        "currency": "INR",
        "products": products,
    }

    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_suffix(".json.tmp")
    with temp_path.open("w", encoding="utf-8") as handle:
        json.dump(snapshot, handle, indent=2)
        handle.write("\n")
    temp_path.replace(path)
    return snapshot


def parse_markdown_file(entry: CorpusEntry, path: Path) -> dict[str, Any]:
    """Parse pricing fields from a saved corpus markdown file."""
    markdown = path.read_text(encoding="utf-8")
    return parse_prices_from_markdown(entry, markdown)
