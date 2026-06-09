"""Build and persist the FAISS vector index from corpus chunks."""

from __future__ import annotations

import json
import logging
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import faiss
import numpy as np

from src.config import INDEX_DIR
from src.ingest.chunker import Chunk, build_url_lookup, chunk_all
from src.ingest.embeddings import Embedder

logger = logging.getLogger(__name__)

FAISS_FILENAME = "faiss.index"
CHUNKS_FILENAME = "chunks.json"
METADATA_FILENAME = "metadata.json"


def build_faiss_index(vectors: np.ndarray) -> faiss.IndexFlatIP:
    """Create a cosine-similarity FAISS index from normalized vectors."""
    index = faiss.IndexFlatIP(vectors.shape[1])
    index.add(vectors)
    return index


def write_index_artifacts(
    target_dir: Path,
    chunks: list[Chunk],
    vectors: np.ndarray,
    embedder: Embedder,
    *,
    ingested_at: str,
) -> None:
    """Write FAISS index, chunk store, and metadata to a directory."""
    target_dir.mkdir(parents=True, exist_ok=True)

    faiss.write_index(build_faiss_index(vectors), str(target_dir / FAISS_FILENAME))

    with (target_dir / CHUNKS_FILENAME).open("w", encoding="utf-8") as handle:
        json.dump([chunk.to_dict() for chunk in chunks], handle, indent=2)
        handle.write("\n")

    metadata = {
        "ingested_at": ingested_at,
        "chunk_count": len(chunks),
        "embedding_provider": embedder.provider,
        "embedding_model": embedder.model_name,
        "embedding_dimension": int(vectors.shape[1]),
        "url_lookup": build_url_lookup(),
    }
    with (target_dir / METADATA_FILENAME).open("w", encoding="utf-8") as handle:
        json.dump(metadata, handle, indent=2)
        handle.write("\n")


def atomic_swap_index(staging_dir: Path, index_dir: Path = INDEX_DIR) -> None:
    """Replace the live index directory with staged artifacts."""
    backup_dir = index_dir.with_name("index.old")
    if not staging_dir.is_dir():
        raise FileNotFoundError(f"Staging directory not found: {staging_dir}")

    if backup_dir.exists():
        shutil.rmtree(backup_dir)

    if index_dir.exists():
        index_dir.rename(backup_dir)

    try:
        staging_dir.rename(index_dir)
    except Exception:
        if backup_dir.exists() and not index_dir.exists():
            backup_dir.rename(index_dir)
        raise
    finally:
        if backup_dir.exists():
            shutil.rmtree(backup_dir)


SAMPLE_SEARCH_QUERIES: tuple[tuple[str, tuple[str, ...], str], ...] = (
    ("expense ratio HDFC Defence Fund", ("summary",), "Defence"),
    ("NAV HDFC Defence Fund Direct Growth", ("summary", "about"), "Defence"),
    ("1 day change HDFC Silver ETF", ("summary", "price_change"), "Silver ETF"),
    ("exit load HDFC Silver ETF FoF", ("exit_load", "about"), "Silver ETF FoF"),
    ("benchmark index HDFC Defence Fund", ("about",), "Defence"),
)


def verify_sample_searches(
    chunks: list[Chunk],
    vectors: np.ndarray,
    embedder: Embedder,
    *,
    top_k: int = 1,
) -> list[dict[str, Any]]:
    """Run sample FAQ queries against an in-memory index before persisting."""
    index = build_faiss_index(vectors)
    chunk_dicts = [chunk.to_dict() for chunk in chunks]
    results: list[dict[str, Any]] = []

    for query, expected_sections, scheme_hint in SAMPLE_SEARCH_QUERIES:
        query_vector = embedder.embed_query(query)
        scores, indices = index.search(query_vector, max(top_k, 3))
        hits = [chunk_dicts[int(idx)] for idx in indices[0] if int(idx) >= 0]
        top = hits[0]
        scheme_ok = scheme_hint.lower() in top["scheme_name"].lower()
        section_ok = any(hit["section"] in expected_sections for hit in hits[:3])
        passed = scheme_ok and section_ok
        status = "PASS" if passed else "WARN"
        results.append(
            {
                "query": query,
                "scheme_name": top["scheme_name"],
                "section": top["section"],
                "score": float(scores[0][0]),
                "passed": passed,
            }
        )
        logger.info(
            "%s sample search: %s -> %s (%s) score=%.3f",
            status,
            query,
            top["scheme_name"],
            top["section"],
            float(scores[0][0]),
        )

    return results


def build_index(index_dir: Path = INDEX_DIR) -> dict[str, Any]:
    """Chunk corpus, embed chunks, and atomically swap in a new index."""
    chunks = chunk_all()
    if not chunks:
        raise RuntimeError("No chunks produced from corpus")

    texts = [chunk.text for chunk in chunks]
    embedder = Embedder.for_texts(texts, chunk_count=len(chunks))
    vectors = embedder.embed_documents(texts)
    ingested_at = datetime.now(timezone.utc).isoformat()
    verification = verify_sample_searches(chunks, vectors, embedder)

    staging_dir = index_dir.with_name("index.staging")
    if staging_dir.exists():
        shutil.rmtree(staging_dir)

    try:
        write_index_artifacts(
            staging_dir,
            chunks,
            vectors,
            embedder,
            ingested_at=ingested_at,
        )
        atomic_swap_index(staging_dir, index_dir)
    except Exception:
        if staging_dir.exists():
            shutil.rmtree(staging_dir)
        raise

    logger.info(
        "Index built with %s chunks using %s (%s-dim) at %s",
        len(chunks),
        embedder.model_name,
        vectors.shape[1],
        index_dir,
    )
    return {
        "chunk_count": len(chunks),
        "ingested_at": ingested_at,
        "index_dir": str(index_dir),
        "embedding_model": embedder.model_name,
        "embedding_provider": embedder.provider,
        "embedding_dimension": int(vectors.shape[1]),
        "sample_search_passed": sum(1 for item in verification if item["passed"]),
        "sample_search_total": len(verification),
    }


def load_embedder(index_dir: Path = INDEX_DIR) -> Embedder:
    """Load the embedder configuration persisted with the index."""
    metadata_path = index_dir / METADATA_FILENAME
    if not metadata_path.is_file():
        raise FileNotFoundError(f"Index metadata not found in {index_dir}. Run the indexer first.")
    with metadata_path.open(encoding="utf-8") as handle:
        metadata = json.load(handle)
    return Embedder.from_metadata(metadata)


def search_index(
    query: str,
    *,
    top_k: int = 5,
    index_dir: Path = INDEX_DIR,
) -> list[dict[str, Any]]:
    """Search the persisted index and return ranked chunk metadata."""
    index_path = index_dir / FAISS_FILENAME
    chunks_path = index_dir / CHUNKS_FILENAME
    if not index_path.is_file() or not chunks_path.is_file():
        raise FileNotFoundError(f"Index not found in {index_dir}. Run the indexer first.")

    with chunks_path.open(encoding="utf-8") as handle:
        chunks = json.load(handle)

    embedder = load_embedder(index_dir)
    query_vector = embedder.embed_query(query)
    index = faiss.read_index(str(index_path))
    scores, indices = index.search(query_vector, top_k)

    results: list[dict[str, Any]] = []
    for score, idx in zip(scores[0], indices[0], strict=False):
        if idx < 0:
            continue
        result = dict(chunks[idx])
        result["score"] = float(score)
        results.append(result)
    return results


def _configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )


def main() -> None:
    """CLI entry point: build the vector index from the corpus."""
    _configure_logging()
    summary = build_index()
    logger.info("Index build complete: %s", summary)


if __name__ == "__main__":
    main()
