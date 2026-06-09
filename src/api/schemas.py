"""Pydantic schemas for the REST API."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator


class HealthResponse(BaseModel):
    status: Literal["ok", "degraded"]
    index_ready: bool
    groq_configured: bool


class ChatRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000)

    @field_validator("question")
    @classmethod
    def strip_non_empty(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("question cannot be empty or whitespace")
        return stripped


class ChatResponse(BaseModel):
    answer: str
    source_url: str | None = None
    last_updated: str | None = None
    is_refusal: bool = False
    is_performance_deflection: bool = False
    product: dict[str, Any] | None = None
    error: str | None = None


class ProductResponse(BaseModel):
    product: dict[str, Any]


class ProductsResponse(BaseModel):
    products: list[dict[str, Any]]
    count: int


class CompareResponse(BaseModel):
    fund_a: dict[str, Any]
    fund_b: dict[str, Any]


class BootstrapResponse(BaseModel):
    suggested_prompts: list[str]
    portfolio: dict[str, Any]
    goal: dict[str, Any]
    allocation: list[dict[str, Any]]
    index_ready: bool
    groq_configured: bool


class IngestionLogResponse(BaseModel):
    latest_run: dict[str, Any] | None = None
    recent_runs: list[dict[str, Any]]
    total_runs: int
    log_path: str
