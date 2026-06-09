"""Tests for the FastAPI REST API."""

from __future__ import annotations

from unittest.mock import patch

from fastapi.testclient import TestClient

from src.api.main import app

client = TestClient(app)


def test_health_endpoint() -> None:
    response = client.get("/api/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] in {"ok", "degraded"}
    assert "index_ready" in payload


def test_bootstrap_endpoint() -> None:
    response = client.get("/api/bootstrap")
    assert response.status_code == 200
    payload = response.json()
    assert len(payload["suggested_prompts"]) >= 3
    assert "portfolio" in payload


def test_products_list() -> None:
    response = client.get("/api/products")
    assert response.status_code == 200
    payload = response.json()
    assert payload["count"] == 12
    assert payload["products"][0]["price_display"].startswith("₹")


def test_product_detail_not_found() -> None:
    response = client.get("/api/products/999")
    assert response.status_code == 404


def test_product_detail_found() -> None:
    response = client.get("/api/products/4")
    assert response.status_code == 200
    assert "Defence" in response.json()["product"]["scheme_name"]


def test_compare_products() -> None:
    response = client.get("/api/compare", params={"a": 4, "b": 2})
    assert response.status_code == 200
    payload = response.json()
    assert "fund_a" in payload and "fund_b" in payload


def test_ingestion_log_endpoint() -> None:
    response = client.get("/api/ingestion", params={"limit": 5})
    assert response.status_code == 200
    payload = response.json()
    assert "recent_runs" in payload
    assert "total_runs" in payload
    assert "log_path" in payload
    assert isinstance(payload["recent_runs"], list)


@patch("src.api.service.answer_query")
def test_chat_endpoint(mock_answer) -> None:
    mock_answer.return_value = (
        "The expense ratio is 0.83%.\n\n"
        "Source: https://groww.in/mutual-funds/hdfc-defence-fund-direct-growth\n\n"
        "Last updated from sources: 05 Jun 2026"
    )
    with patch("src.api.service.index_ready", return_value=True):
        with patch("src.api.service.groq_configured", return_value=True):
            response = client.post(
                "/api/chat",
                json={"question": "What is the expense ratio of HDFC Defence Fund?"},
            )
    assert response.status_code == 200
    payload = response.json()
    assert "0.83%" in payload["answer"]
    assert payload["source_url"] is not None
    assert not payload["is_refusal"]


@patch("src.api.service.answer_query")
def test_chat_refusal(mock_answer) -> None:
    mock_answer.return_value = (
        "I understand you're looking for guidance. "
        "I can only answer factual questions about HDFC schemes from official Groww pages.\n\n"
        "For general mutual fund education, visit: https://www.amfiindia.com/investor-corner"
    )
    with patch("src.api.service.index_ready", return_value=True):
        with patch("src.api.service.groq_configured", return_value=True):
            response = client.post(
                "/api/chat",
                json={"question": "Should I invest in HDFC Gold ETF FoF?"},
            )
    assert response.status_code == 200
    assert response.json()["is_refusal"] is True
