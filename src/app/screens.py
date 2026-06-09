"""Screen renderers for each navigation tab."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import streamlit as st

from src.app import components as ui
from src.app.data import (
    all_products,
    entry_by_id,
    product_by_id,
    search_products,
)
from src.config import CORPUS_ENTRIES


def render_header(title: str) -> None:
    """Large title for the active screen."""
    st.markdown(f'<p class="hdfc-large-title">{title}</p>', unsafe_allow_html=True)
    st.markdown(ui.disclaimer_banner(), unsafe_allow_html=True)


def render_home(*, on_ask_ai) -> None:
    render_header("Home")
    st.markdown(ui.portfolio_widget(), unsafe_allow_html=True)
    st.markdown(ui.goal_card(), unsafe_allow_html=True)
    st.markdown(
        ui.ai_insight_card(
            "Ask about HDFC schemes",
            f"Explore {len(CORPUS_ENTRIES)} HDFC funds, ETFs, and stocks with "
            "facts-only answers from Groww.",
        ),
        unsafe_allow_html=True,
    )
    if st.button("Ask AI", type="primary", use_container_width=True, key="home_ask_ai"):
        on_ask_ai()


def render_chat(
    *,
    messages: list[dict[str, Any]],
    suggested_prompts: list[str],
    on_prompt: Callable[[str], None],
    loading: bool,
) -> None:
    render_header("Chat")
    if not messages:
        st.markdown(
            ui.ai_insight_card(
                "Welcome",
                "Ask factual questions about expense ratio, NAV, exit load, benchmarks, "
                "and minimum SIP for HDFC schemes.",
            ),
            unsafe_allow_html=True,
        )

    st.markdown("**Suggested prompts**")
    cols = st.columns(2)
    for index, prompt in enumerate(suggested_prompts):
        col = cols[index % 2]
        with col:
            if st.button(prompt, key=f"prompt_{index}", use_container_width=True):
                on_prompt(prompt)

    st.markdown(ui.chat_thread(messages), unsafe_allow_html=True)

    if loading:
        st.markdown(ui.loading_skeleton(), unsafe_allow_html=True)

    for message in messages:
        if message.get("role") == "assistant" and message.get("product"):
            st.markdown(ui.fund_card(message["product"]), unsafe_allow_html=True)


def render_discover(*, on_select) -> None:
    render_header("Discover")
    query = st.text_input(
        "Search funds",
        placeholder="Search by name or type…",
        label_visibility="collapsed",
        key="discover_search",
    )
    filter_type = st.segmented_control(
        "Category",
        options=["All", "Mutual Fund", "ETF", "Stock"],
        default="All",
        key="discover_filter",
    )

    products = search_products(query)
    if filter_type != "All":
        type_map = {
            "Mutual Fund": "mutual_fund",
            "ETF": "etf",
            "Stock": "stock",
        }
        target = type_map.get(filter_type, "")
        products = [p for p in products if p.get("product_type") == target]

    st.markdown(ui.fund_grid(products), unsafe_allow_html=True)

    st.markdown("**Select a fund for details**")
    options = {p["scheme_name"]: p["id"] for p in all_products()}
    selected = st.selectbox(
        "Fund",
        options=list(options.keys()),
        label_visibility="collapsed",
        key="discover_select",
    )
    if st.button("View details", key="discover_view", use_container_width=True):
        on_select(options[selected])


def render_fund_detail(product_id: int | None, *, on_back) -> None:
    render_header("Fund Details")
    if product_id is None:
        st.info("Select a fund from Discover to view details.")
        return

    product = product_by_id(product_id)
    entry = entry_by_id(product_id)
    if not product or not entry:
        st.warning("Fund not found.")
        return

    if st.button("← Back to Discover", key="detail_back"):
        on_back()

    st.markdown(ui.fund_detail_card(product), unsafe_allow_html=True)
    st.markdown(
        f'<p class="hdfc-footnote">Source: <a href="{entry.source_url}" '
        f'style="color:var(--color-primary);">{entry.source_url}</a></p>',
        unsafe_allow_html=True,
    )


def render_compare() -> None:
    render_header("Compare")
    st.markdown(
        '<p class="hdfc-body" style="color:var(--color-text-secondary);margin-bottom:16px;">'
        "Side-by-side factual fields — not investment advice.</p>",
        unsafe_allow_html=True,
    )

    products = all_products()
    names = [p["scheme_name"] for p in products]
    col1, col2 = st.columns(2)
    with col1:
        name_a = st.selectbox("Fund A", names, index=3, key="compare_a")
    with col2:
        name_b = st.selectbox("Fund B", names, index=1, key="compare_b")

    product_a = next(p for p in products if p["scheme_name"] == name_a)
    product_b = next(p for p in products if p["scheme_name"] == name_b)
    st.markdown(ui.comparison_card(product_a, product_b), unsafe_allow_html=True)


def render_portfolio() -> None:
    render_header("Portfolio")
    st.markdown(
        '<p class="hdfc-caption">DEMO DATA — no login or PII collected</p>',
        unsafe_allow_html=True,
    )
    st.markdown(ui.portfolio_widget(), unsafe_allow_html=True)
    st.markdown(ui.allocation_chart(), unsafe_allow_html=True)
    st.markdown(
        ui.ai_insight_card(
            "SIP calendar",
            "Demo view — connect a broker account on Groww to manage real SIPs.",
        ),
        unsafe_allow_html=True,
    )


def render_learn() -> None:
    render_header("Learn")
    st.markdown(ui.learn_cards(), unsafe_allow_html=True)
