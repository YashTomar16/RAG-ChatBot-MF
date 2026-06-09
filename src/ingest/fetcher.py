"""Fetch Groww pages, convert to markdown, and refresh price snapshots."""

from __future__ import annotations

import hashlib
import logging
import re
import time
from dataclasses import dataclass

import httpx
from bs4 import BeautifulSoup
from markdownify import markdownify

from src.config import CORPUS_DIR, CORPUS_ENTRIES, CorpusEntry, corpus_file_path
from src.ingest.price_parser import (
    parse_prices_from_html,
    parse_prices_from_markdown,
    update_price_snapshots,
)

logger = logging.getLogger(__name__)

DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/136.0.0.0 Safari/537.36"
)
REQUEST_DELAY_SECONDS = 1.5
REQUEST_TIMEOUT_SECONDS = 30.0


@dataclass
class FetchResult:
    entry: CorpusEntry
    success: bool
    changed: bool
    skipped: bool = False
    error: str | None = None


def _extract_title(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    if soup.title and soup.title.string:
        return soup.title.string.strip()
    return "Untitled Groww Page"


def _html_to_markdown(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()

    main = soup.find("main") or soup.body or soup
    markdown = markdownify(str(main), heading_style="ATX", bullets="-")
    markdown = re.sub(r"\n{3,}", "\n\n", markdown)
    return markdown.strip()


def _build_markdown_document(source_url: str, title: str, body: str) -> str:
    return f"Source URL: {source_url}\nTitle: {title}\n\n{body.strip()}\n"


def _content_hash(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def fetch_page(client: httpx.Client, entry: CorpusEntry) -> tuple[str, str]:
    """Fetch HTML for a Groww corpus URL."""
    response = client.get(entry.source_url, follow_redirects=True)
    response.raise_for_status()
    html = response.text
    title = _extract_title(html)
    return html, title


def save_corpus_markdown(
    entry: CorpusEntry,
    title: str,
    body_markdown: str,
    *,
    skip_if_unchanged: bool = True,
) -> bool:
    """
    Write markdown to the corpus directory.

    Returns True if the file was written, False if unchanged and skipped.
    """
    document = _build_markdown_document(entry.source_url, title, body_markdown)
    output_path = corpus_file_path(entry)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if skip_if_unchanged and output_path.is_file():
        existing_hash = _content_hash(output_path.read_text(encoding="utf-8"))
        new_hash = _content_hash(document)
        if existing_hash == new_hash:
            logger.info("Unchanged, skipping write: %s", output_path.name)
            return False

    output_path.write_text(document, encoding="utf-8")
    logger.info("Saved corpus file: %s", output_path.name)
    return True


def fetch_and_save_entry(
    client: httpx.Client,
    entry: CorpusEntry,
    *,
    skip_if_unchanged: bool = True,
) -> tuple[FetchResult, dict | None]:
    """Fetch one Groww page, save markdown, and return parsed price fields."""
    try:
        html, title = fetch_page(client, entry)
        body_markdown = _html_to_markdown(html)
        changed = save_corpus_markdown(
            entry,
            title,
            body_markdown,
            skip_if_unchanged=skip_if_unchanged,
        )
        saved_markdown = corpus_file_path(entry).read_text(encoding="utf-8")
        parsed = parse_prices_from_markdown(entry, saved_markdown)
        if not parsed:
            parsed = parse_prices_from_html(entry, html)
        return FetchResult(entry=entry, success=True, changed=changed), parsed
    except Exception as exc:
        logger.exception("Failed to fetch %s", entry.source_url)
        return FetchResult(entry=entry, success=False, changed=False, error=str(exc)), None


def fetch_all(
    *,
    skip_if_unchanged: bool = True,
    delay_seconds: float = REQUEST_DELAY_SECONDS,
) -> list[FetchResult]:
    """Fetch all 12 Groww URLs and update price snapshots."""
    results: list[FetchResult] = []
    parsed_by_id: dict[int, dict] = {}

    headers = {"User-Agent": DEFAULT_USER_AGENT}
    with httpx.Client(headers=headers, timeout=REQUEST_TIMEOUT_SECONDS) as client:
        for index, entry in enumerate(CORPUS_ENTRIES):
            if index > 0:
                time.sleep(delay_seconds)

            result, parsed = fetch_and_save_entry(
                client,
                entry,
                skip_if_unchanged=skip_if_unchanged,
            )
            results.append(result)

            if parsed:
                parsed_by_id[entry.id] = parsed
            elif result.success:
                logger.warning("Price parse returned no fields for %s", entry.source_url)

    if parsed_by_id:
        update_price_snapshots(parsed_by_id)
    else:
        logger.warning("No price fields parsed; leaving price_snapshots.json unchanged")

    return results


def refresh_prices_from_corpus() -> None:
    """Re-parse pricing fields from existing corpus markdown files."""
    parsed_by_id: dict[int, dict] = {}
    for entry in CORPUS_ENTRIES:
        path = corpus_file_path(entry)
        if not path.is_file():
            logger.warning("Missing corpus file for %s", entry.local_file)
            continue
        try:
            markdown = path.read_text(encoding="utf-8")
            parsed = parse_prices_from_markdown(entry, markdown)
            if parsed:
                parsed_by_id[entry.id] = parsed
            else:
                logger.warning("No price fields parsed from %s", path.name)
        except Exception:
            logger.exception("Failed to parse prices from %s", path.name)

    if parsed_by_id:
        update_price_snapshots(parsed_by_id)


def _configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )


def main() -> None:
    """CLI entry point: fetch all Groww pages and refresh price snapshots."""
    _configure_logging()
    CORPUS_DIR.mkdir(parents=True, exist_ok=True)

    results = fetch_all()
    successes = sum(1 for result in results if result.success)
    failures = [result for result in results if not result.success]

    logger.info("Fetch complete: %s/%s succeeded", successes, len(results))
    for result in failures:
        logger.error("Failed: %s — %s", result.entry.source_url, result.error)

    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
