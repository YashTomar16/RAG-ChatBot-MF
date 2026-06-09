"""Local and cloud embedding providers for the vector index."""

from __future__ import annotations

import logging
from functools import lru_cache
from typing import Literal

import faiss
import numpy as np

from src.config import EMBEDDING_MODEL, EMBEDDING_PROVIDER, OPENAI_API_KEY

logger = logging.getLogger(__name__)

EmbeddingProvider = Literal["bge", "openai"]

BGE_SMALL_MODEL = "BAAI/bge-small-en-v1.5"
BGE_LARGE_MODEL = "BAAI/bge-large-en-v1.5"
BGE_QUERY_INSTRUCTION = "Represent this sentence for searching relevant passages: "

# Prefer BGE-small for compact FAQ corpora; switch to large when scale/complexity grows.
BGE_SMALL_MAX_CHUNKS = 100
BGE_SMALL_MAX_AVG_TOKENS = 400


def _count_tokens(text: str) -> int:
    try:
        import tiktoken

        encoder = tiktoken.get_encoding("cl100k_base")
        return len(encoder.encode(text))
    except Exception:
        return int(len(text.split()) * 1.35)


def select_bge_model(
    texts: list[str],
    *,
    chunk_count: int | None = None,
) -> str:
    """Choose BGE-small or BGE-large based on stored chunk volume and size."""
    count = chunk_count if chunk_count is not None else len(texts)
    if count == 0:
        return BGE_SMALL_MODEL

    token_counts = [_count_tokens(text) for text in texts]
    avg_tokens = sum(token_counts) / len(token_counts)
    max_tokens = max(token_counts)

    if count <= BGE_SMALL_MAX_CHUNKS and avg_tokens <= BGE_SMALL_MAX_AVG_TOKENS and max_tokens <= 600:
        logger.info(
            "Selected %s for %s chunks (avg %.0f tokens, max %s tokens)",
            BGE_SMALL_MODEL,
            count,
            avg_tokens,
            max_tokens,
        )
        return BGE_SMALL_MODEL

    logger.info(
        "Selected %s for %s chunks (avg %.0f tokens, max %s tokens)",
        BGE_LARGE_MODEL,
        count,
        avg_tokens,
        max_tokens,
    )
    return BGE_LARGE_MODEL


def resolve_embedding_model(texts: list[str], *, chunk_count: int | None = None) -> tuple[str, EmbeddingProvider]:
    """Resolve the embedding model and provider from config and chunk stats."""
    provider: EmbeddingProvider = EMBEDDING_PROVIDER  # type: ignore[assignment]

    if provider == "openai":
        return EMBEDDING_MODEL, provider

    if EMBEDDING_MODEL in {"auto", "bge-auto"}:
        return select_bge_model(texts, chunk_count=chunk_count), "bge"

    if EMBEDDING_MODEL in {BGE_SMALL_MODEL, BGE_LARGE_MODEL}:
        return EMBEDDING_MODEL, "bge"

    if EMBEDDING_MODEL in {"bge-small", "bge_small", "small"}:
        return BGE_SMALL_MODEL, "bge"

    if EMBEDDING_MODEL in {"bge-large", "bge_large", "large"}:
        return BGE_LARGE_MODEL, "bge"

    # Default: local BGE with auto selection.
    return select_bge_model(texts, chunk_count=chunk_count), "bge"


@lru_cache(maxsize=2)
def _load_sentence_transformer(model_name: str):
    from sentence_transformers import SentenceTransformer

    logger.info("Loading sentence-transformers model: %s", model_name)
    return SentenceTransformer(model_name)


def _normalize_vectors(matrix: np.ndarray) -> np.ndarray:
    vectors = np.array(matrix, dtype=np.float32)
    faiss.normalize_L2(vectors)
    return vectors


class Embedder:
    """Embed documents and queries with a consistent model configuration."""

    def __init__(self, model_name: str, provider: EmbeddingProvider):
        self.model_name = model_name
        self.provider = provider

    @classmethod
    def for_texts(cls, texts: list[str], *, chunk_count: int | None = None) -> Embedder:
        model_name, provider = resolve_embedding_model(texts, chunk_count=chunk_count)
        return cls(model_name=model_name, provider=provider)

    @classmethod
    def from_metadata(cls, metadata: dict) -> Embedder:
        return cls(
            model_name=metadata["embedding_model"],
            provider=metadata.get("embedding_provider", "bge"),
        )

    def embed_documents(self, texts: list[str], batch_size: int = 32) -> np.ndarray:
        if not texts:
            raise ValueError("Cannot embed an empty document list")

        if self.provider == "openai":
            return _normalize_vectors(_embed_openai(texts, batch_size=batch_size))

        model = _load_sentence_transformer(self.model_name)
        vectors = model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=len(texts) > 32,
            normalize_embeddings=True,
        )
        return np.array(vectors, dtype=np.float32)

    def embed_query(self, query: str) -> np.ndarray:
        if self.provider == "openai":
            return _normalize_vectors(_embed_openai([query], batch_size=1))

        model = _load_sentence_transformer(self.model_name)
        query_text = f"{BGE_QUERY_INSTRUCTION}{query}"
        vector = model.encode(
            [query_text],
            normalize_embeddings=True,
        )
        return np.array(vector, dtype=np.float32)


def _embed_openai(texts: list[str], batch_size: int = 32) -> np.ndarray:
    if not OPENAI_API_KEY:
        raise RuntimeError(
            "OPENAI_API_KEY is not set. Use EMBEDDING_PROVIDER=bge for free local embeddings."
        )

    from openai import OpenAI

    client = OpenAI(api_key=OPENAI_API_KEY)
    vectors: list[list[float]] = []
    for start in range(0, len(texts), batch_size):
        batch = texts[start : start + batch_size]
        response = client.embeddings.create(model=EMBEDDING_MODEL, input=batch)
        ordered = sorted(response.data, key=lambda item: item.index)
        vectors.extend(item.embedding for item in ordered)
    return np.array(vectors, dtype=np.float32)
