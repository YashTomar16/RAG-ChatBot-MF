"""Read and parse corpus markdown files into structured document objects."""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from pathlib import Path

from src.config import (
    CORPUS_BY_LOCAL_FILE,
    CORPUS_DIR,
    CORPUS_ENTRIES,
    ProductType,
    corpus_file_path,
)

logger = logging.getLogger(__name__)

HEADER_SOURCE_PATTERN = re.compile(r"^Source URL:\s*(.+)\s*$")
HEADER_TITLE_PATTERN = re.compile(r"^Title:\s*(.+)\s*$")


@dataclass(frozen=True)
class CorpusDocument:
    """Structured representation of one ingested Groww markdown file."""

    source_url: str
    title: str
    scheme_name: str
    product_type: ProductType
    local_file: str
    body: str
    file_path: Path


def parse_header(markdown: str) -> tuple[str, str, str]:
    """
    Parse canonical header from markdown content.

    Returns (source_url, title, body).
    """
    lines = markdown.splitlines()
    if len(lines) < 2:
        raise ValueError("Corpus file missing canonical header")

    source_match = HEADER_SOURCE_PATTERN.match(lines[0])
    title_match = HEADER_TITLE_PATTERN.match(lines[1])
    if not source_match or not title_match:
        raise ValueError("Corpus file header must start with Source URL and Title lines")

    body_start = 2
    while body_start < len(lines) and not lines[body_start].strip():
        body_start += 1

    body = "\n".join(lines[body_start:])
    return source_match.group(1).strip(), title_match.group(1).strip(), body


def load_document(path: Path) -> CorpusDocument:
    """Load and parse a single corpus markdown file."""
    markdown = path.read_text(encoding="utf-8")
    source_url, title, body = parse_header(markdown)
    local_file = path.name

    entry = CORPUS_BY_LOCAL_FILE.get(local_file)
    if entry is None:
        raise ValueError(f"No corpus registry entry for file: {local_file}")

    if entry.source_url != source_url:
        logger.warning(
            "Source URL mismatch in %s: file=%s registry=%s",
            local_file,
            source_url,
            entry.source_url,
        )

    return CorpusDocument(
        source_url=source_url,
        title=title,
        scheme_name=entry.scheme_name,
        product_type=entry.product_type,
        local_file=local_file,
        body=body,
        file_path=path,
    )


def load_all(corpus_dir: Path = CORPUS_DIR) -> list[CorpusDocument]:
    """Load all registered corpus markdown files in registry order."""
    documents: list[CorpusDocument] = []
    for entry in CORPUS_ENTRIES:
        path = corpus_file_path(entry)
        if not path.is_file():
            raise FileNotFoundError(f"Missing corpus file: {path}")
        documents.append(load_document(path))
    return documents


def _configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )


def main() -> None:
    """CLI entry point: load corpus files and print summary metadata."""
    _configure_logging()
    documents = load_all()

    for document in documents:
        body_chars = len(document.body)
        logger.info(
            "%s | %s | %s | %s chars",
            document.product_type,
            document.scheme_name,
            document.source_url,
            body_chars,
        )

    logger.info("Loaded %s corpus documents from %s", len(documents), CORPUS_DIR)


if __name__ == "__main__":
    main()
