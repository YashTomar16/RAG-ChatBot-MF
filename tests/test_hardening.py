"""Phase 7 hardening — error handling and ingestion resilience."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import httpx
import pytest
from fastapi.testclient import TestClient

from src.api.main import app
from src.api.service import chat
from src.config import CORPUS_ENTRIES
from src.ingest.fetcher import fetch_and_save_entry
from src.ingest.indexer import FAISS_FILENAME, METADATA_FILENAME, atomic_swap_index, write_index_artifacts
from src.rag.generator import generate_answer
from src.rag.retriever import RetrievalResult

client = TestClient(app)


def test_pipeline_empty_query_validation() -> None:
    from src.rag.pipeline import answer_query

    response = answer_query("   ")
    assert "enter a factual question" in response.lower()


def test_api_chat_rejects_whitespace_question() -> None:
    response = client.post("/api/chat", json={"question": "   "})
    assert response.status_code == 422


def test_api_chat_missing_groq_key() -> None:
    with patch("src.api.service.groq_configured", return_value=False):
        with patch("src.api.service.index_ready", return_value=True):
            result = chat("What is the expense ratio of HDFC Defence Fund?")
    assert result.get("error") == "groq_missing"
    assert "GROQ_API_KEY" in result["answer"]


def test_api_chat_missing_index() -> None:
    with patch("src.api.service.index_ready", return_value=False):
        result = chat("What is the expense ratio of HDFC Defence Fund?")
    assert result.get("error") == "index_missing"


@patch("src.rag.generator._call_groq_llm")
def test_generator_timeout_fallback(mock_call) -> None:
    mock_call.return_value = (
        "The answer service is taking longer than expected. "
        "Please try again in a moment or rephrase your factual question."
    )
    retrieval = RetrievalResult(
        chunks=[{"text": "Expense ratio 0.83%", "section": "summary"}],
        citation_chunk={"source_url": "https://groww.in/mutual-funds/hdfc-defence-fund-direct-growth"},
        structured_price=None,
        detected_scheme=None,
        insufficient_context=False,
        needs_disambiguation=False,
        ingested_at="2026-06-08T07:27:03.556464+00:00",
    )
    answer = generate_answer("expense ratio?", retrieval)
    assert "longer than expected" in answer.lower()


@patch("groq.Groq")
@patch("src.rag.generator.GROQ_API_KEY", "gsk-test")
@patch("src.rag.generator.LLM_PROVIDER", "groq")
def test_groq_timeout_returns_template(mock_groq_cls) -> None:
    from src.rag.generator import _call_groq_llm

    mock_client = MagicMock()
    mock_groq_cls.return_value = mock_client
    mock_client.chat.completions.create.side_effect = TimeoutError("Request timed out")

    result = _call_groq_llm("Question: test\n\nContext:\nchunk")
    assert "longer than expected" in result.lower()


def test_fetch_failure_preserves_existing_corpus(tmp_path, monkeypatch) -> None:
    entry = CORPUS_ENTRIES[0]
    corpus_dir = tmp_path / "groww"
    corpus_dir.mkdir()
    output_path = corpus_dir / entry.local_file
    original = "Source URL: x\nTitle: y\n\nOriginal content preserved.\n"
    output_path.write_text(original, encoding="utf-8")

    monkeypatch.setattr("src.ingest.fetcher.corpus_file_path", lambda e: corpus_dir / e.local_file)

    mock_client = MagicMock()
    mock_client.get.side_effect = httpx.TimeoutException("timeout")

    result, parsed = fetch_and_save_entry(mock_client, entry)
    assert not result.success
    assert output_path.read_text(encoding="utf-8") == original
    assert parsed is None


def test_atomic_swap_replaces_index(tmp_path) -> None:
    import numpy as np

    from src.ingest.embeddings import Embedder

    index_dir = tmp_path / "index"
    staging_dir = tmp_path / "index.staging"
    embedder = Embedder.from_metadata(
        {"embedding_provider": "bge", "embedding_model": "BAAI/bge-small-en-v1.5", "embedding_dimension": 384}
    )
    vectors = np.ones((1, 384), dtype="float32")

    write_index_artifacts(
        index_dir,
        [],
        vectors,
        embedder,
        ingested_at="2026-06-01T00:00:00+00:00",
    )
    assert (index_dir / FAISS_FILENAME).is_file()

    write_index_artifacts(
        staging_dir,
        [],
        vectors,
        embedder,
        ingested_at="2026-06-09T00:00:00+00:00",
    )
    atomic_swap_index(staging_dir, index_dir)

    with (index_dir / METADATA_FILENAME).open(encoding="utf-8") as handle:
        metadata = json.load(handle)
    assert metadata["ingested_at"] == "2026-06-09T00:00:00+00:00"


def test_atomic_swap_restores_on_failure(tmp_path) -> None:
    index_dir = tmp_path / "index"
    index_dir.mkdir()
    (index_dir / FAISS_FILENAME).write_text("live", encoding="utf-8")
    missing_staging = tmp_path / "missing.staging"

    with pytest.raises(FileNotFoundError):
        atomic_swap_index(missing_staging, index_dir)

    assert (index_dir / FAISS_FILENAME).read_text(encoding="utf-8") == "live"


def test_footer_uses_ingested_at_from_index(tmp_path) -> None:
    import numpy as np

    from src.ingest.embeddings import Embedder
    from src.ingest.indexer import CHUNKS_FILENAME, load_embedder

    index_dir = tmp_path / "index"
    embedder = Embedder.from_metadata(
        {"embedding_provider": "bge", "embedding_model": "BAAI/bge-small-en-v1.5", "embedding_dimension": 384}
    )
    vectors = np.ones((1, 384), dtype="float32")
    ingested_at = "2026-06-09T12:00:00+00:00"

    write_index_artifacts(
        index_dir,
        [],
        vectors,
        embedder,
        ingested_at=ingested_at,
    )

    with (index_dir / METADATA_FILENAME).open(encoding="utf-8") as handle:
        metadata = json.load(handle)
    assert metadata["ingested_at"] == ingested_at
    assert (index_dir / CHUNKS_FILENAME).is_file()
    loaded = load_embedder(index_dir)
    assert loaded.model_name == "BAAI/bge-small-en-v1.5"
