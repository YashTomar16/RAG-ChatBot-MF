"""Section-first chunking for Groww corpus markdown."""

from __future__ import annotations

import json
import logging
import re
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.config import PRICE_SNAPSHOTS_PATH, ProductType
from src.ingest.loader import CorpusDocument, load_all

logger = logging.getLogger(__name__)

MAX_SECTION_TOKENS = 600
OVERLAP_TOKENS = 50

SKIP_HEADING_PATTERNS: tuple[str, ...] = (
    r"return calculator",
    r"^holdings\b",
    r"compare similar",
    r"fund house",
    r"fund management",
    r"^category returns",
    r"similar etf",
    r"similar stock",
    r"about groww",
    r"selection based on fund size",
    r"shareholding pattern",
    r"financial performance",
    r"returns and rankings",
    r"^mutual funds invested",
    r"understand terms",
)

SECTION_TAG_RULES: tuple[tuple[str, str], ...] = (
    (r"minimum investment", "min_investment"),
    (r"exit load", "exit_load"),
    (r"^fundamentals", "fundamentals"),
    (r"^performance", "price_change"),
    (r"^about\b", "about"),
)

HEADING_PATTERN = re.compile(r"^(#{2,3})\s+(.+)$", re.MULTILINE)
SUBHEADING_PATTERN = re.compile(r"^(#{4,5})\s+(.+)$", re.MULTILINE)
LINK_PATTERN = re.compile(r"\[([^\]]+)\]\([^)]+\)")


@dataclass
class Chunk:
    """Searchable text chunk with citation and retrieval metadata."""

    chunk_id: str
    text: str
    source_url: str
    scheme_name: str
    product_type: ProductType
    section: str
    local_file: str
    ingested_at: str
    nav: float | None = None
    nav_date: str | None = None
    current_price: float | None = None
    change_1d_pct: float | None = None
    expense_ratio_pct: float | None = None

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        return {key: value for key, value in data.items() if value is not None}


def _count_tokens(text: str) -> int:
    try:
        import tiktoken

        encoder = tiktoken.get_encoding("cl100k_base")
        return len(encoder.encode(text))
    except Exception:
        return int(len(text.split()) * 1.35)


def _clean_markdown(text: str) -> str:
    text = LINK_PATTERN.sub(r"\1", text)
    text = text.replace("\\-", "-")
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _strip_site_boilerplate(body: str) -> str:
    match = re.search(r"^#\s", body, flags=re.MULTILINE)
    if not match:
        return body
    return body[match.start() :].strip()


def _normalize_heading_title(title: str) -> str:
    """Strip repeated markdown heading markers produced by HTML conversion."""
    return re.sub(r"^#+\s*", "", title.strip())


def _should_skip_heading(title: str) -> bool:
    lowered = _normalize_heading_title(title).lower().strip()
    return any(re.search(pattern, lowered) for pattern in SKIP_HEADING_PATTERNS)


def _section_tag(title: str) -> str | None:
    lowered = _normalize_heading_title(title).lower().strip()
    if _should_skip_heading(title):
        return None
    for pattern, tag in SECTION_TAG_RULES:
        if re.search(pattern, lowered):
            return tag
    return None


def _load_price_snapshots_by_file() -> dict[str, dict[str, Any]]:
    if not PRICE_SNAPSHOTS_PATH.is_file():
        return {}
    with PRICE_SNAPSHOTS_PATH.open(encoding="utf-8") as handle:
        payload = json.load(handle)
    return {product["local_file"]: product for product in payload.get("products", [])}


def _attach_pricing_fields(chunk: Chunk, snapshot: dict[str, Any] | None) -> None:
    if not snapshot:
        return
    if chunk.section in {"summary", "price_change", "fundamentals"}:
        for field_name in (
            "nav",
            "nav_date",
            "current_price",
            "change_1d_pct",
            "expense_ratio_pct",
        ):
            if field_name in snapshot:
                setattr(chunk, field_name, snapshot[field_name])


def _split_with_overlap(text: str, max_tokens: int, overlap_tokens: int) -> list[str]:
    paragraphs = [part.strip() for part in re.split(r"\n\s*\n", text) if part.strip()]
    if not paragraphs:
        return []

    chunks: list[str] = []
    current: list[str] = []
    current_tokens = 0

    for paragraph in paragraphs:
        paragraph_tokens = _count_tokens(paragraph)
        if current and current_tokens + paragraph_tokens > max_tokens:
            chunks.append("\n\n".join(current))
            if overlap_tokens > 0 and current:
                overlap_text: list[str] = []
                overlap_count = 0
                for item in reversed(current):
                    overlap_count += _count_tokens(item)
                    overlap_text.insert(0, item)
                    if overlap_count >= overlap_tokens:
                        break
                current = overlap_text
                current_tokens = sum(_count_tokens(item) for item in current)
            else:
                current = []
                current_tokens = 0

        current.append(paragraph)
        current_tokens += paragraph_tokens

        if paragraph_tokens > max_tokens:
            chunks.append(paragraph)
            current = []
            current_tokens = 0

    if current:
        joined = "\n\n".join(current)
        if not chunks or chunks[-1] != joined:
            chunks.append(joined)

    return chunks


def _split_section_text(text: str) -> list[str]:
    if _count_tokens(text) <= MAX_SECTION_TOKENS:
        return [text]

    subsections = SUBHEADING_PATTERN.split(text)
    if len(subsections) > 1:
        parts: list[str] = []
        buffer = ""
        for part in subsections:
            if part.startswith("####"):
                if buffer.strip():
                    parts.extend(_split_with_overlap(buffer.strip(), MAX_SECTION_TOKENS, OVERLAP_TOKENS))
                buffer = part + "\n"
            else:
                buffer += part
        if buffer.strip():
            parts.extend(_split_with_overlap(buffer.strip(), MAX_SECTION_TOKENS, OVERLAP_TOKENS))
        return parts

    return _split_with_overlap(text, MAX_SECTION_TOKENS, OVERLAP_TOKENS)


def _extract_hero_and_remainder(clean_body: str) -> tuple[str, str]:
    lines = clean_body.splitlines()
    title_index = next(
        (index for index, line in enumerate(lines) if line.startswith("# ") and not line.startswith("## ")),
        0,
    )
    end_index = len(lines)
    for index in range(title_index + 1, len(lines)):
        if lines[index].startswith("### ") or lines[index].startswith("## "):
            end_index = index
            break
    hero = "\n".join(lines[:end_index]).strip()
    remainder = "\n".join(lines[end_index:]).strip()
    return hero, remainder


def _iter_sections(text: str) -> list[tuple[int, str, str]]:
    matches = list(HEADING_PATTERN.finditer(text))
    if not matches:
        return []

    sections: list[tuple[int, str, str]] = []
    for index, match in enumerate(matches):
        level = len(match.group(1))
        title = _normalize_heading_title(match.group(2))
        if not title:
            continue
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        content = text[start:end].strip()
        sections.append((level, title, content))
    return sections


def _trim_about_groww(content: str) -> str:
    match = re.search(r"^#{1,5}\s+About Groww", content, flags=re.MULTILINE | re.IGNORECASE)
    if match:
        return content[: match.start()].strip()
    return content


def chunk_document(
    document: CorpusDocument,
    *,
    ingested_at: str | None = None,
    snapshot: dict[str, Any] | None = None,
) -> list[Chunk]:
    """Split one corpus document into section-first chunks."""
    ingested_at = ingested_at or datetime.now(timezone.utc).isoformat()
    clean_body = _clean_markdown(_strip_site_boilerplate(document.body))
    hero, remainder = _extract_hero_and_remainder(clean_body)

    chunks: list[Chunk] = []
    chunk_index = 0

    def add_chunk(section: str, text: str) -> None:
        nonlocal chunk_index
        for piece in _split_section_text(text.strip()):
            if not piece.strip():
                continue
            chunk = Chunk(
                chunk_id=f"{document.local_file}:{section}:{chunk_index}",
                text=piece.strip(),
                source_url=document.source_url,
                scheme_name=document.scheme_name,
                product_type=document.product_type,
                section=section,
                local_file=document.local_file,
                ingested_at=ingested_at,
            )
            _attach_pricing_fields(chunk, snapshot)
            chunks.append(chunk)
            chunk_index += 1

    if hero:
        add_chunk("summary", hero)

    skip_until_level: int | None = None
    for level, title, content in _iter_sections(remainder):
        if level == 2:
            skip_until_level = 2 if _should_skip_heading(title) else None

        tagged_section = _section_tag(title)
        in_skip_zone = skip_until_level is not None and level >= skip_until_level
        if in_skip_zone and not (level == 3 and tagged_section is not None):
            continue

        if _should_skip_heading(title):
            continue

        section = tagged_section
        if section is None:
            continue

        section_content = f"{'#' * level} {title}\n\n{content}".strip()
        if section == "about":
            section_content = _trim_about_groww(section_content)
            if not section_content.strip():
                continue

        add_chunk(section, section_content)

    return chunks


def chunk_all(documents: list[CorpusDocument] | None = None) -> list[Chunk]:
    """Chunk all loaded corpus documents."""
    documents = documents or load_all()
    snapshots = _load_price_snapshots_by_file()
    ingested_at = datetime.now(timezone.utc).isoformat()
    all_chunks: list[Chunk] = []
    for document in documents:
        snapshot = snapshots.get(document.local_file)
        document_chunks = chunk_document(
            document,
            ingested_at=ingested_at,
            snapshot=snapshot,
        )
        logger.info(
            "Chunked %s -> %s chunks",
            document.local_file,
            len(document_chunks),
        )
        all_chunks.extend(document_chunks)
    return all_chunks


def build_url_lookup() -> dict[str, str]:
    """Map scheme names and common aliases to Groww URLs."""
    from src.config import build_scheme_url_lookup

    return build_scheme_url_lookup()


def _configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )


def main() -> None:
    """CLI entry point: chunk corpus and print summary."""
    _configure_logging()
    chunks = chunk_all()
    by_section: dict[str, int] = {}
    for chunk in chunks:
        by_section[chunk.section] = by_section.get(chunk.section, 0) + 1

    logger.info("Total chunks: %s", len(chunks))
    for section, count in sorted(by_section.items()):
        logger.info("  %s: %s", section, count)


if __name__ == "__main__":
    main()
