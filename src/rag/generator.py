"""LLM answer generation from retrieved context via Groq."""

from __future__ import annotations

import logging
import os
from typing import Any

from src.config import GROQ_API_KEY, LLM_MODEL, LLM_PROVIDER
from src.rag.retriever import RetrievalResult

logger = logging.getLogger(__name__)

GROQ_TIMEOUT_SECONDS = float(os.getenv("GROQ_TIMEOUT_SECONDS", "30"))

SYSTEM_PROMPT = """You are a facts-only HDFC mutual fund FAQ assistant.
Answer using ONLY the provided context chunks and structured price data.
Rules:
- Maximum 3 sentences.
- No investment advice, opinions, or recommendations.
- No return calculations, CAGR, or performance comparisons.
- For NAV/price answers, use structured price data when present; state values and dates exactly as shown.
- If structured price data is present, treat it as authoritative over chunk text.
- Do not invent numbers, URLs, or facts not in the context.
- Output answer text only. Do not include source links or footers.
"""


def _format_context_chunks(chunks: list[dict[str, Any]]) -> str:
    blocks: list[str] = []
    for index, chunk in enumerate(chunks, start=1):
        header = (
            f"[Chunk {index}] scheme={chunk.get('scheme_name', '')} "
            f"section={chunk.get('section', '')}"
        )
        blocks.append(f"{header}\n{chunk.get('text', '').strip()}")
    return "\n\n".join(blocks)


def _template_insufficient() -> str:
    return (
        "I don't have enough information in the ingested Groww corpus to answer that question. "
        "Please try naming a specific HDFC scheme from our supported list."
    )


def _template_disambiguation() -> str:
    return (
        "Multiple HDFC schemes may match your question. "
        "Please specify the exact scheme name so I can provide an accurate factual answer."
    )


def _template_timeout() -> str:
    return (
        "The answer service is taking longer than expected. "
        "Please try again in a moment or rephrase your factual question."
    )


def _call_groq_llm(user_prompt: str) -> str:
    if not GROQ_API_KEY:
        raise RuntimeError(
            "GROQ_API_KEY is not set. Add it to .env to generate factual answers."
        )
    if LLM_PROVIDER != "groq":
        raise RuntimeError(
            f"Unsupported LLM_PROVIDER={LLM_PROVIDER!r}. Only 'groq' is configured."
        )

    from groq import Groq

    client = Groq(api_key=GROQ_API_KEY, timeout=GROQ_TIMEOUT_SECONDS)
    try:
        response = client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.0,
            max_tokens=250,
        )
    except Exception as exc:
        logger.exception("Groq LLM call failed")
        message = str(exc).lower()
        if "timeout" in message or "timed out" in message:
            return _template_timeout()
        raise RuntimeError(f"LLM request failed: {exc}") from exc
    content = response.choices[0].message.content
    if not content or not content.strip():
        raise RuntimeError("LLM returned an empty answer.")
    return content.strip()


def generate_answer(
    query: str,
    retrieval: RetrievalResult,
) -> str:
    """Generate a facts-only answer from retrieved context."""
    if retrieval.insufficient_context:
        return _template_insufficient()
    if retrieval.needs_disambiguation:
        return _template_disambiguation()
    if not retrieval.chunks:
        return _template_insufficient()

    context = _format_context_chunks(retrieval.chunks)
    user_prompt = f"Question: {query}\n\nContext:\n{context}"
    return _call_groq_llm(user_prompt)
