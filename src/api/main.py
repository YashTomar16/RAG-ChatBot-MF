"""FastAPI REST API for Railway deployment."""

from __future__ import annotations

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from src.api import service
from src.api.schemas import (
    BootstrapResponse,
    ChatRequest,
    ChatResponse,
    CompareResponse,
    HealthResponse,
    IngestionLogResponse,
    ProductResponse,
    ProductsResponse,
)

app = FastAPI(
    title="HDFC Mutual Fund FAQ API",
    description="Facts-only RAG backend for the HDFC Groww corpus assistant.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=service.cors_origins(),
    allow_origin_regex=r"https://.*\.vercel\.app$",
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


@app.get("/api/health", response_model=HealthResponse)
def health() -> HealthResponse:
    index_ready = service.index_ready()
    groq_configured = service.groq_configured()
    status = "ok" if index_ready and groq_configured else "degraded"
    return HealthResponse(
        status=status,
        index_ready=index_ready,
        groq_configured=groq_configured,
    )


@app.get("/api/bootstrap", response_model=BootstrapResponse)
def bootstrap() -> BootstrapResponse:
    return BootstrapResponse(**service.bootstrap_payload())


@app.get("/api/ingestion", response_model=IngestionLogResponse)
def ingestion_log(limit: int = Query(10, ge=1, le=100)) -> IngestionLogResponse:
    return IngestionLogResponse(**service.ingestion_log_payload(limit=limit))


@app.get("/api/products", response_model=ProductsResponse)
def products(
    q: str = Query("", description="Search by scheme name or type"),
    type: str = Query("all", description="Filter: all, mutual_fund, etf, stock"),
) -> ProductsResponse:
    items = service.list_products(query=q, product_type=type)
    return ProductsResponse(products=items, count=len(items))


@app.get("/api/products/{product_id}", response_model=ProductResponse)
def product_detail(product_id: int) -> ProductResponse:
    item = service.get_product(product_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return ProductResponse(product=item)


@app.get("/api/compare", response_model=CompareResponse)
def compare(
    a: int = Query(..., description="First product id"),
    b: int = Query(..., description="Second product id"),
) -> CompareResponse:
    result = service.compare_products(a, b)
    if result is None:
        raise HTTPException(status_code=404, detail="One or both products not found")
    return CompareResponse(**result)


@app.post("/api/chat", response_model=ChatResponse)
def chat(body: ChatRequest) -> ChatResponse:
    return ChatResponse(**service.chat(body.question))


@app.get("/")
def root() -> dict[str, str]:
    return {"service": "HDFC Mutual Fund FAQ API", "docs": "/docs"}
