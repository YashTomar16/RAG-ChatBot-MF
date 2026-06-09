"""Business logic for HTTP API handlers."""

from __future__ import annotations

import os
from typing import Any

from src.api.serializers import (
    SUGGESTED_PROMPTS,
    mock_allocation_payload,
    mock_goal_payload,
    mock_portfolio_payload,
    serialize_product,
)
from src.app.data import all_products, detect_product_from_text, product_by_id, search_products
from src.app.parse import parse_response
from src.config import GROQ_API_KEY, INDEX_DIR, INGESTION_LOG_PATH
from src.ingest.indexer import CHUNKS_FILENAME, FAISS_FILENAME
from src.rag.pipeline import answer_query
from src.scheduler.ingestion_log import load_ingestion_log, latest_ingestion_run, recent_ingestion_runs


def index_ready() -> bool:
    return (
        (INDEX_DIR / FAISS_FILENAME).is_file()
        and (INDEX_DIR / CHUNKS_FILENAME).is_file()
    )


def groq_configured() -> bool:
    return bool(GROQ_API_KEY)


def list_products(*, query: str = "", product_type: str | None = None) -> list[dict[str, Any]]:
    products = search_products(query)
    if product_type and product_type != "all":
        products = [p for p in products if p.get("product_type") == product_type]
    return [serialize_product(product) for product in products]


def get_product(product_id: int) -> dict[str, Any] | None:
    product = product_by_id(product_id)
    if product is None:
        return None
    return serialize_product(product)


def compare_products(product_id_a: int, product_id_b: int) -> dict[str, Any] | None:
    product_a = get_product(product_id_a)
    product_b = get_product(product_id_b)
    if not product_a or not product_b:
        return None
    return {"fund_a": product_a, "fund_b": product_b}


def chat(question: str) -> dict[str, Any]:
    question = question.strip()
    if not question:
        return {
            "answer": "Please enter a factual question about an HDFC scheme from our Groww corpus.",
            "source_url": None,
            "last_updated": None,
            "is_refusal": False,
            "is_performance_deflection": False,
            "product": None,
        }

    if not index_ready():
        return {
            "answer": "Vector index not found. Run the ingestion pipeline on the server first.",
            "source_url": None,
            "last_updated": None,
            "is_refusal": False,
            "is_performance_deflection": False,
            "product": None,
            "error": "index_missing",
        }

    if not groq_configured():
        return {
            "answer": "GROQ_API_KEY is not configured on the server.",
            "source_url": None,
            "last_updated": None,
            "is_refusal": False,
            "is_performance_deflection": False,
            "product": None,
            "error": "groq_missing",
        }

    raw = answer_query(question)
    parsed = parse_response(raw)
    product = detect_product_from_text(question)
    return {
        "answer": parsed.body,
        "source_url": parsed.source_url,
        "last_updated": parsed.last_updated,
        "is_refusal": parsed.is_refusal,
        "is_performance_deflection": parsed.is_performance_deflection,
        "product": serialize_product(product) if product and not parsed.is_refusal else None,
    }


def bootstrap_payload() -> dict[str, Any]:
    return {
        "suggested_prompts": SUGGESTED_PROMPTS,
        "portfolio": mock_portfolio_payload(),
        "goal": mock_goal_payload(),
        "allocation": mock_allocation_payload(),
        "index_ready": index_ready(),
        "groq_configured": groq_configured(),
    }


def ingestion_log_payload(*, limit: int = 10) -> dict[str, Any]:
    log = load_ingestion_log()
    runs = log.get("runs", [])
    return {
        "latest_run": latest_ingestion_run(),
        "recent_runs": recent_ingestion_runs(limit=limit),
        "total_runs": len(runs),
        "log_path": str(INGESTION_LOG_PATH),
    }


def cors_origins() -> list[str]:
    raw = os.getenv(
        "CORS_ORIGINS",
        "http://localhost:5173,http://localhost:3000",
    )
    return [origin.strip() for origin in raw.split(",") if origin.strip()]
