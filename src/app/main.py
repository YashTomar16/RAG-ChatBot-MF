"""Streamlit UI — legacy local dev. Primary UI: React frontend (frontend/)."""

from __future__ import annotations

import logging
from typing import Any

import streamlit as st

from src.app.data import detect_product_from_text
from src.app.parse import ParsedResponse, parse_response
from src.app.screens import (
    render_chat,
    render_compare,
    render_discover,
    render_fund_detail,
    render_home,
    render_learn,
    render_portfolio,
)
from src.app.styles import inject_styles
from src.config import GROQ_API_KEY, INDEX_DIR
from src.ingest.indexer import CHUNKS_FILENAME, FAISS_FILENAME
from src.rag.pipeline import answer_query

logger = logging.getLogger(__name__)

MAIN_TABS = ("home", "discover", "chat", "portfolio", "learn")
TAB_LABELS = {
    "home": "Home",
    "discover": "Discover",
    "chat": "Chat",
    "portfolio": "Portfolio",
    "learn": "Learn",
    "compare": "Compare",
    "detail": "Fund Details",
}

SUGGESTED_PROMPTS = [
    "What is the expense ratio of HDFC Defence Fund Direct Growth?",
    "What is the minimum SIP for HDFC Gold ETF FoF?",
    "What is the exit load on HDFC Silver ETF FoF Direct Growth?",
    "What is the latest NAV of HDFC Defence Fund Direct Growth?",
    "What is the risk category of HDFC Balanced Advantage Fund?",
    "What is the 1-day change for HDFC Silver ETF?",
]


def _init_session_state() -> None:
    defaults: dict[str, Any] = {
        "active_tab": "chat",
        "dark_mode": False,
        "messages": [],
        "selected_product_id": None,
        "pending_prompt": None,
        "loading_response": False,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


@st.cache_resource
def ensure_index_ready() -> bool:
    """Verify the vector index exists (lazy warm-up on first query)."""
    return (
        (INDEX_DIR / FAISS_FILENAME).is_file()
        and (INDEX_DIR / CHUNKS_FILENAME).is_file()
    )


def _set_tab(tab: str) -> None:
    st.session_state.active_tab = tab
    st.rerun()


def _select_fund(product_id: int) -> None:
    st.session_state.selected_product_id = product_id
    st.session_state.active_tab = "detail"
    st.rerun()


def _queue_prompt(prompt: str) -> None:
    st.session_state.pending_prompt = prompt
    st.rerun()


def _process_question(question: str) -> None:
    question = question.strip()
    if not question:
        return

    st.session_state.messages.append({"role": "user", "content": question})

    try:
        if not ensure_index_ready():
            raise FileNotFoundError(
                "Vector index not found. Run: python -m src.ingest.indexer"
            )
        if not GROQ_API_KEY:
            raise RuntimeError(
                "GROQ_API_KEY is not set. Add it to .env for factual answers."
            )

        raw = answer_query(question)
        parsed = parse_response(raw)
        product = detect_product_from_text(question)

        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": parsed.body,
                "parsed": parsed,
                "product": product if not parsed.is_refusal else None,
            }
        )
    except Exception as exc:
        logger.exception("Query failed")
        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": f"Sorry, something went wrong: {exc}",
                "parsed": ParsedResponse(
                    body=str(exc),
                    source_url=None,
                    last_updated=None,
                    is_refusal=False,
                    is_performance_deflection=False,
                    raw=str(exc),
                ),
                "product": None,
            }
        )


def _render_bottom_nav() -> None:
    st.markdown("---")
    cols = st.columns(len(MAIN_TABS))
    for col, tab in zip(cols, MAIN_TABS, strict=True):
        with col:
            label = TAB_LABELS[tab]
            is_active = st.session_state.active_tab == tab
            if st.button(
                label,
                key=f"nav_{tab}",
                type="primary" if is_active else "secondary",
                use_container_width=True,
            ):
                if tab != st.session_state.active_tab:
                    _set_tab(tab)


def _render_active_screen() -> None:
    tab = st.session_state.active_tab

    if tab == "home":
        render_home(on_ask_ai=lambda: _set_tab("chat"))
    elif tab == "discover":
        render_discover(on_select=_select_fund)
    elif tab == "detail":
        render_fund_detail(
            st.session_state.selected_product_id,
            on_back=lambda: _set_tab("discover"),
        )
    elif tab == "chat":
        render_chat(
            messages=st.session_state.messages,
            suggested_prompts=SUGGESTED_PROMPTS,
            on_prompt=_queue_prompt,
            loading=False,
        )
        if prompt := st.chat_input("Ask a factual question about HDFC schemes…"):
            _process_question(prompt)
            st.rerun()
    elif tab == "portfolio":
        render_portfolio()
    elif tab == "learn":
        render_learn()
    elif tab == "compare":
        render_compare()
    else:
        st.session_state.active_tab = "chat"
        st.rerun()


def main() -> None:
    st.set_page_config(
        page_title="HDFC Mutual Fund Assistant",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="collapsed",
    )
    _init_session_state()

    _, col_theme = st.columns([5, 1])
    with col_theme:
        st.session_state.dark_mode = st.toggle(
            "Dark",
            value=st.session_state.dark_mode,
            key="dark_mode_toggle",
        )

    inject_styles(dark_mode=st.session_state.dark_mode)

    if st.session_state.pending_prompt:
        prompt = st.session_state.pending_prompt
        st.session_state.pending_prompt = None
        if st.session_state.active_tab != "chat":
            st.session_state.active_tab = "chat"
        _process_question(prompt)
        st.rerun()

    if st.session_state.active_tab in MAIN_TABS and st.session_state.active_tab != "chat":
        _, compare_btn = st.columns([4, 1])
        with compare_btn:
            if st.button("Compare funds", key="open_compare", use_container_width=True):
                _set_tab("compare")

    _render_active_screen()
    _render_bottom_nav()


if __name__ == "__main__":
    main()
