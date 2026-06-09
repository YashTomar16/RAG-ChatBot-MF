"""Corpus URL registry — re-exports from config for ingest modules."""

from src.config import (
    CORPUS_BY_LOCAL_FILE,
    CORPUS_BY_URL,
    CORPUS_ENTRIES,
    CORPUS_URL_WHITELIST,
    CorpusEntry,
    corpus_file_path,
    is_whitelisted_url,
)

__all__ = [
    "CORPUS_ENTRIES",
    "CORPUS_URL_WHITELIST",
    "CORPUS_BY_URL",
    "CORPUS_BY_LOCAL_FILE",
    "CorpusEntry",
    "corpus_file_path",
    "is_whitelisted_url",
]
