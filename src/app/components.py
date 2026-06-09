"""HTML UI components for the Streamlit app."""

from __future__ import annotations

import html
from typing import Any

from src.app.data import (
    MOCK_ALLOCATION,
    MOCK_GOAL,
    MOCK_PORTFOLIO,
    PRODUCT_TYPE_LABELS,
    format_change,
    format_price,
)
from src.app.parse import ParsedResponse


def _esc(value: object) -> str:
    return html.escape(str(value))


def disclaimer_banner() -> str:
    return """
    <div class="hdfc-disclaimer" role="note" aria-label="Disclaimer">
        <strong>Facts-only. No investment advice.</strong>
        <p class="hdfc-footnote" style="margin-top:4px;">
            Answers are sourced from official Groww pages for 12 HDFC schemes.
        </p>
    </div>
    """


def ai_insight_card(title: str, body: str) -> str:
    return f"""
    <div class="hdfc-card hdfc-glass">
        <p class="hdfc-caption">AI INSIGHT</p>
        <p class="hdfc-title-2" style="font-size:18px;margin:8px 0 4px;">{_esc(title)}</p>
        <p class="hdfc-body" style="font-size:15px;color:var(--color-text-secondary);">
            {_esc(body)}
        </p>
    </div>
    """


def fund_card(product: dict[str, Any], *, compact: bool = False) -> str:
    name = _esc(product.get("scheme_name", "Unknown"))
    ptype = product.get("product_type", "")
    badge = _esc(PRODUCT_TYPE_LABELS.get(ptype, ptype))
    price = _esc(format_price(product))
    change_text, change_class = format_change(product)
    change_html = (
        f'<span class="hdfc-change {change_class}">{_esc(change_text)}</span>'
    )
    expense = product.get("expense_ratio_pct")
    expense_html = ""
    if expense is not None and not compact:
        expense_html = (
            f'<p class="hdfc-footnote" style="margin-top:8px;">'
            f"Expense ratio: {_esc(f'{expense}%')}</p>"
        )
    aum = product.get("aum_cr") or product.get("market_cap_cr")
    aum_html = ""
    if aum is not None and not compact:
        label = "AUM" if product.get("aum_cr") else "Market cap"
        aum_html = (
            f'<p class="hdfc-footnote">{label}: {_esc(f"₹{aum:,.0f} Cr")}</p>'
        )

    return f"""
    <div class="hdfc-card hdfc-fund-card">
        <span class="hdfc-badge">{badge}</span>
        <p class="hdfc-title-2" style="font-size:17px;">{name}</p>
        <div class="hdfc-price-row">
            <span class="hdfc-price">{price}</span>
            {change_html}
        </div>
        {expense_html}
        {aum_html}
    </div>
    """


def fund_grid(products: list[dict[str, Any]]) -> str:
    if not products:
        return '<p class="hdfc-footnote">No funds match your search.</p>'
    cards = "".join(fund_card(product, compact=True) for product in products)
    return f'<div class="hdfc-fund-grid">{cards}</div>'


def portfolio_widget() -> str:
    gain = MOCK_PORTFOLIO["value"] - MOCK_PORTFOLIO["invested"]
    gain_class = "hdfc-gain-positive" if gain >= 0 else "hdfc-gain-negative"
    sign = "+" if gain >= 0 else ""
    return f"""
    <div class="hdfc-card">
        <p class="hdfc-caption">DEMO PORTFOLIO</p>
        <p class="hdfc-portfolio-value">₹{MOCK_PORTFOLIO["value"]:,.0f}</p>
        <p class="{gain_class}">{sign}₹{abs(gain):,.0f} ({MOCK_PORTFOLIO["xirr"]}% XIRR)</p>
        <p class="hdfc-footnote">Invested ₹{MOCK_PORTFOLIO["invested"]:,.0f} · {MOCK_PORTFOLIO["period"]}</p>
    </div>
    """


def goal_card() -> str:
    progress = min(100, int(MOCK_GOAL["current"] / MOCK_GOAL["target"] * 100))
    return f"""
    <div class="hdfc-card">
        <p class="hdfc-caption">GOAL PROGRESS</p>
        <p class="hdfc-title-2" style="font-size:18px;">{_esc(MOCK_GOAL["name"])}</p>
        <div class="hdfc-progress-track" role="progressbar" aria-valuenow="{progress}">
            <div class="hdfc-progress-fill" style="width:{progress}%;"></div>
        </div>
        <p class="hdfc-footnote">
            ₹{MOCK_GOAL["current"]:,.0f} of ₹{MOCK_GOAL["target"]:,.0f} · Target {MOCK_GOAL["deadline"]}
        </p>
    </div>
    """


def allocation_chart() -> str:
    gradient_parts = []
    start = 0.0
    for _label, pct, color in MOCK_ALLOCATION:
        end = start + pct
        gradient_parts.append(f"{color} {start}% {end}%")
        start = end
    gradient = ", ".join(gradient_parts)
    legend = "".join(
        f"""
        <div class="hdfc-legend-item">
            <span class="hdfc-legend-dot" style="background:{color};"></span>
            <span>{_esc(label)} · {pct}%</span>
        </div>
        """
        for label, pct, color in MOCK_ALLOCATION
    )
    return f"""
    <div class="hdfc-card">
        <p class="hdfc-title-2" style="font-size:18px;margin-bottom:12px;">Allocation</p>
        <div class="hdfc-donut-wrap">
            <div class="hdfc-donut" style="background:conic-gradient({gradient});"
                 role="img" aria-label="Portfolio allocation chart"></div>
            <div class="hdfc-legend">{legend}</div>
        </div>
    </div>
    """


def chat_bubble(role: str, content: str, *, parsed: ParsedResponse | None = None) -> str:
    bubble_class = role
    if parsed and parsed.is_refusal:
        bubble_class = "refusal"

    citation_html = ""
    if parsed and parsed.source_url:
        citation_html = f"""
        <div class="hdfc-citation">
            <a href="{_esc(parsed.source_url)}" target="_blank" rel="noopener">
                Source: Groww
            </a>
            {f"<br>Last updated: {_esc(parsed.last_updated)}" if parsed.last_updated else ""}
        </div>
        """

    return f"""
    <div class="hdfc-bubble-row {role}">
        <div class="hdfc-bubble {bubble_class}" role="article">
            {_esc(content)}
            {citation_html}
        </div>
    </div>
    """


def chat_thread(messages: list[dict[str, Any]]) -> str:
    if not messages:
        return ""
    rows = []
    for message in messages:
        parsed = message.get("parsed")
        if isinstance(parsed, ParsedResponse):
            body = parsed.body
        else:
            body = message.get("content", "")
        rows.append(chat_bubble(message["role"], body, parsed=parsed))
    return f'<div class="hdfc-chat-thread">{"".join(rows)}</div>'


def loading_skeleton() -> str:
    return """
    <div class="hdfc-bubble-row assistant">
        <div class="hdfc-skeleton" aria-label="Loading response"></div>
    </div>
    """


def comparison_card(product_a: dict[str, Any], product_b: dict[str, Any]) -> str:
    fields: list[tuple[str, str, str]] = []

    def _val(product: dict[str, Any], key: str, fmt: str = "{}") -> str:
        value = product.get(key)
        if value is None:
            return "—"
        return fmt.format(value)

    fields.append(("NAV / Price", format_price(product_a), format_price(product_b)))
    fields.append((
        "1D change",
        format_change(product_a)[0],
        format_change(product_b)[0],
    ))
    fields.append((
        "Expense ratio",
        _val(product_a, "expense_ratio_pct", "{}%"),
        _val(product_b, "expense_ratio_pct", "{}%"),
    ))
    aum_a = product_a.get("aum_cr") or product_a.get("market_cap_cr")
    aum_b = product_b.get("aum_cr") or product_b.get("market_cap_cr")
    fields.append((
        "AUM / Market cap",
        f"₹{aum_a:,.0f} Cr" if aum_a else "—",
        f"₹{aum_b:,.0f} Cr" if aum_b else "—",
    ))

    rows = ""
    for label, val_a, val_b in fields:
        rows += f"""
        <div class="hdfc-compare-field">
            <div class="hdfc-compare-label">{_esc(label)}</div>
            <div class="hdfc-compare-grid">
                <div class="hdfc-compare-value">{_esc(val_a)}</div>
                <div class="hdfc-compare-value">{_esc(val_b)}</div>
            </div>
        </div>
        """

    return f"""
    <div class="hdfc-card">
        <div class="hdfc-compare-grid" style="margin-bottom:12px;">
            <div class="hdfc-compare-header">{_esc(product_a.get("scheme_name", ""))}</div>
            <div class="hdfc-compare-header">{_esc(product_b.get("scheme_name", ""))}</div>
        </div>
        {rows}
        <p class="hdfc-footnote" style="margin-top:12px;">
            Factual comparison only — not a recommendation.
        </p>
    </div>
    """


def fund_detail_card(product: dict[str, Any]) -> str:
    url = product.get("source_url", "")
    link_html = ""
    if url:
        link_html = f"""
        <p style="margin-top:12px;">
            <a href="{_esc(url)}" target="_blank" rel="noopener"
               style="color:var(--color-primary);text-decoration:none;font:var(--text-subhead);">
                View returns &amp; performance on Groww →
            </a>
        </p>
        """
    return fund_card(product) + link_html


def learn_cards() -> str:
    cards = [
        (
            "Understanding expense ratio",
            "The annual fee charged by a fund, expressed as a percentage of assets.",
        ),
        (
            "What is exit load?",
            "A fee levied when you redeem units within a specified period.",
        ),
        (
            "Risk categories",
            "SEBI-mandated riskometer levels from Low to Very High.",
        ),
    ]
    html_parts = []
    for title, body in cards:
        html_parts.append(f"""
        <div class="hdfc-card">
            <p class="hdfc-title-2" style="font-size:17px;">{_esc(title)}</p>
            <p class="hdfc-footnote" style="margin-top:6px;">{_esc(body)}</p>
        </div>
        """)
    resources = """
    <div class="hdfc-card hdfc-glass">
        <p class="hdfc-title-2" style="font-size:17px;">Official resources</p>
        <p class="hdfc-footnote" style="margin-top:8px;">
            <a href="https://www.amfiindia.com/investor-corner" target="_blank"
               style="color:var(--color-primary);">AMFI Investor Corner</a>
            ·
            <a href="https://investor.sebi.gov.in" target="_blank"
               style="color:var(--color-primary);">SEBI Investor Education</a>
        </p>
    </div>
    """
    return "".join(html_parts) + resources
