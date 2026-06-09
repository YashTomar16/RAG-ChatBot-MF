"""Inject Apple HIG + Groww design tokens into Streamlit."""

from __future__ import annotations

from pathlib import Path

import streamlit as st

from src.config import PROJECT_ROOT

TOKENS_PATH = PROJECT_ROOT / "Docs" / "design-system" / "tokens.css"


def _load_tokens() -> str:
    return TOKENS_PATH.read_text(encoding="utf-8")


def inject_styles(*, dark_mode: bool) -> None:
    """Apply design system CSS to the Streamlit app."""
    theme = "dark" if dark_mode else "light"
    tokens = _load_tokens()
    st.markdown(
        f"""
        <style>
        {tokens}

        /* Streamlit chrome overrides */
        [data-testid="stAppViewContainer"] {{
            background-color: var(--color-bg);
        }}
        [data-testid="stHeader"] {{
            background: transparent;
        }}
        [data-testid="stToolbar"] {{
            display: none;
        }}
        .main .block-container {{
            max-width: 768px;
            padding-top: 1rem;
            padding-bottom: 5.5rem;
        }}
        [data-testid="stAppViewContainer"][data-theme="{theme}"] {{
            color: var(--color-text-primary);
        }}

        /* App shell */
        .hdfc-app {{
            font-family: var(--font-family);
            color: var(--color-text-primary);
        }}
        .hdfc-large-title {{
            font: var(--text-large-title);
            margin: 0 0 var(--space-sm) 0;
            letter-spacing: -0.02em;
        }}
        .hdfc-title-2 {{
            font: var(--text-title-2);
            margin: 0;
        }}
        .hdfc-body {{
            font: var(--text-body);
            margin: 0;
        }}
        .hdfc-footnote {{
            font: var(--text-footnote);
            color: var(--color-text-secondary);
            margin: 0;
        }}
        .hdfc-caption {{
            font: var(--text-caption);
            color: var(--color-text-secondary);
        }}

        /* Disclaimer */
        .hdfc-disclaimer {{
            background: var(--color-surface);
            border-left: 4px solid var(--color-warning);
            border-radius: var(--radius-sm);
            padding: var(--space-sm) var(--space-md);
            margin-bottom: var(--space-md);
            box-shadow: var(--shadow-sm);
        }}
        .hdfc-disclaimer strong {{
            font: var(--text-subhead);
            color: var(--color-text-primary);
        }}

        /* Cards */
        .hdfc-card {{
            background: var(--color-surface);
            border-radius: var(--radius-lg);
            padding: var(--space-md);
            box-shadow: var(--shadow-sm);
            margin-bottom: var(--space-md);
            transition: box-shadow var(--motion-fast);
        }}
        .hdfc-card:hover {{
            box-shadow: var(--shadow-md);
        }}
        .hdfc-glass {{
            background: var(--color-glass);
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            border: 1px solid var(--color-separator);
        }}

        /* Fund card */
        .hdfc-fund-card {{
            cursor: default;
        }}
        .hdfc-badge {{
            display: inline-block;
            font: var(--text-caption);
            background: var(--color-primary-muted);
            color: var(--color-primary);
            padding: 2px 8px;
            border-radius: 999px;
            margin-bottom: var(--space-sm);
        }}
        .hdfc-price-row {{
            display: flex;
            align-items: baseline;
            gap: var(--space-sm);
            margin-top: var(--space-sm);
        }}
        .hdfc-price {{
            font: var(--text-headline);
        }}
        .hdfc-change {{
            font: var(--text-footnote);
            padding: 2px 8px;
            border-radius: 999px;
        }}
        .hdfc-change.gain {{
            color: var(--color-success);
            background: rgba(0, 200, 83, 0.12);
        }}
        .hdfc-change.loss {{
            color: var(--color-error);
            background: rgba(229, 57, 53, 0.12);
        }}
        .hdfc-change.neutral {{
            color: var(--color-text-secondary);
        }}

        /* Chat */
        .hdfc-chat-thread {{
            display: flex;
            flex-direction: column;
            gap: var(--space-md);
            margin: var(--space-md) 0;
        }}
        .hdfc-bubble-row {{
            display: flex;
            width: 100%;
        }}
        .hdfc-bubble-row.user {{
            justify-content: flex-end;
        }}
        .hdfc-bubble-row.assistant {{
            justify-content: flex-start;
        }}
        .hdfc-bubble {{
            max-width: 85%;
            padding: 12px 16px;
            border-radius: var(--radius-md);
            font: var(--text-body);
            white-space: pre-wrap;
            word-wrap: break-word;
        }}
        .hdfc-bubble.user {{
            background: var(--color-primary-muted);
            border-bottom-right-radius: 4px;
        }}
        .hdfc-bubble.assistant {{
            background: var(--color-surface);
            box-shadow: var(--shadow-sm);
            border-bottom-left-radius: 4px;
        }}
        .hdfc-bubble.refusal {{
            border: 1px solid var(--color-warning);
        }}
        .hdfc-citation {{
            margin-top: var(--space-sm);
            padding-top: var(--space-sm);
            border-top: 1px solid var(--color-separator);
            font: var(--text-footnote);
            color: var(--color-text-secondary);
        }}
        .hdfc-citation a {{
            color: var(--color-primary);
            text-decoration: none;
        }}
        .hdfc-skeleton {{
            background: linear-gradient(
                90deg,
                var(--color-separator) 25%,
                var(--color-surface-elevated) 50%,
                var(--color-separator) 75%
            );
            background-size: 200% 100%;
            animation: hdfc-shimmer 1.2s infinite;
            border-radius: var(--radius-md);
            height: 48px;
            max-width: 70%;
        }}
        @keyframes hdfc-shimmer {{
            0% {{ background-position: 200% 0; }}
            100% {{ background-position: -200% 0; }}
        }}
        @media (prefers-reduced-motion: reduce) {{
            .hdfc-skeleton {{ animation: none; }}
        }}

        /* Portfolio widget */
        .hdfc-portfolio-value {{
            font: var(--text-title-1);
            margin: var(--space-sm) 0;
        }}
        .hdfc-gain-positive {{
            color: var(--color-success);
            font: var(--text-headline);
        }}
        .hdfc-gain-negative {{
            color: var(--color-error);
            font: var(--text-headline);
        }}

        /* Goal progress */
        .hdfc-progress-track {{
            background: var(--color-separator);
            border-radius: 999px;
            height: 8px;
            margin: var(--space-sm) 0;
            overflow: hidden;
        }}
        .hdfc-progress-fill {{
            background: var(--color-primary);
            height: 100%;
            border-radius: 999px;
            transition: width var(--motion-normal);
        }}

        /* Comparison */
        .hdfc-compare-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: var(--space-md);
        }}
        .hdfc-compare-header {{
            font: var(--text-headline);
            text-align: center;
            padding-bottom: var(--space-sm);
            border-bottom: 1px solid var(--color-separator);
        }}
        .hdfc-compare-field {{
            padding: var(--space-sm) 0;
            border-bottom: 1px solid var(--color-separator);
        }}
        .hdfc-compare-label {{
            font: var(--text-caption);
            color: var(--color-text-secondary);
            text-transform: uppercase;
            letter-spacing: 0.04em;
        }}
        .hdfc-compare-value {{
            font: var(--text-callout);
            margin-top: 2px;
        }}

        /* Donut chart */
        .hdfc-donut-wrap {{
            display: flex;
            align-items: center;
            gap: var(--space-lg);
            flex-wrap: wrap;
        }}
        .hdfc-donut {{
            width: 120px;
            height: 120px;
            border-radius: 50%;
            flex-shrink: 0;
        }}
        .hdfc-legend {{
            flex: 1;
            min-width: 140px;
        }}
        .hdfc-legend-item {{
            display: flex;
            align-items: center;
            gap: var(--space-sm);
            margin-bottom: var(--space-sm);
            font: var(--text-subhead);
        }}
        .hdfc-legend-dot {{
            width: 10px;
            height: 10px;
            border-radius: 50%;
            flex-shrink: 0;
        }}

        /* Grid */
        .hdfc-fund-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
            gap: var(--space-md);
        }}

        /* Nav hint */
        .hdfc-nav-hint {{
            text-align: center;
            font: var(--text-caption);
            color: var(--color-text-secondary);
            padding: var(--space-sm);
        }}

        /* Streamlit button theming */
        div[data-testid="stHorizontalBlock"] button[kind="secondary"] {{
            border-radius: var(--radius-sm);
            border-color: var(--color-separator);
        }}
        div[data-testid="stChatInput"] textarea {{
            border-radius: var(--radius-md) !important;
        }}
        </style>
        <div data-theme="{theme}" class="hdfc-app"></div>
        """,
        unsafe_allow_html=True,
    )
