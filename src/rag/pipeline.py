"""End-to-end query orchestration: classify, retrieve, generate, and format."""

from __future__ import annotations

import logging

from src.rag.classifier import classify
from src.rag.formatter import format_from_retrieval
from src.rag.generator import generate_answer
from src.rag.retriever import retrieve
from src.refusal.handler import route_query

logger = logging.getLogger(__name__)


def answer_query(question: str) -> str:
    """Answer a user question through the full RAG or refusal pipeline."""
    question = question.strip()
    if not question:
        return (
            "Please enter a factual question about an HDFC scheme from our Groww corpus."
        )

    route = route_query(question)
    if not route.proceed_to_rag:
        return route.response or "I can only answer factual questions about HDFC schemes."

    classification = classify(question)
    retrieval = retrieve(question, classification)
    answer = generate_answer(question, retrieval)
    return format_from_retrieval(
        answer,
        retrieval.citation_chunk,
        retrieval.ingested_at,
    )


def _configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )


def main() -> None:
    """CLI entry point for manual pipeline testing."""
    import sys

    _configure_logging()
    if len(sys.argv) < 2:
        print("Usage: python -m src.rag.pipeline \"your question here\"")
        raise SystemExit(1)
    print(answer_query(" ".join(sys.argv[1:])))


if __name__ == "__main__":
    main()
