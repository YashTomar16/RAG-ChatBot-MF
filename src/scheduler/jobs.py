"""APScheduler jobs for 8x/day corpus and index refresh (IST)."""

from __future__ import annotations

import argparse
import logging
import threading
from dataclasses import dataclass
from datetime import datetime

import pytz
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from src.config import TIMEZONE
from src.ingest.fetcher import fetch_all
from src.ingest.indexer import build_index
from src.scheduler.ingestion_log import IngestionLogEntry, append_ingestion_run

logger = logging.getLogger(__name__)

# 09:15, 12:15, 15:15, 18:15, 21:15, 00:15, 03:15, 06:15 IST (8 runs/day)
INGESTION_CRON_HOURS = "0,3,6,9,12,15,18,21"
INGESTION_CRON_MINUTE = 15
JOB_ID = "corpus_ingestion"

_ingestion_lock = threading.Lock()


@dataclass
class IngestionResult:
    """Outcome of a single ingestion cycle."""

    started_at: str
    finished_at: str
    success: bool
    fetch_successes: int
    fetch_failures: int
    ingested_at: str | None = None
    chunk_count: int | None = None
    error: str | None = None


def _result_to_log_entry(result: IngestionResult) -> IngestionLogEntry:
    return IngestionLogEntry(
        started_at=result.started_at,
        finished_at=result.finished_at,
        success=result.success,
        fetch_successes=result.fetch_successes,
        fetch_failures=result.fetch_failures,
        ingested_at=result.ingested_at,
        chunk_count=result.chunk_count,
        error=result.error,
    )


def run_ingestion() -> IngestionResult:
    """
    Fetch Groww pages, refresh prices, re-chunk, re-embed, and atomically swap index.

    Online queries continue using the previous index until the swap completes.
    Per-URL fetch failures are logged but do not abort the run; a failed index
    build leaves the previous index intact (atomic swap in ``build_index``).
    Each run is appended to ``data/ingestion_log.json``.
    """
    result = _execute_ingestion()
    append_ingestion_run(_result_to_log_entry(result))
    return result


def _execute_ingestion() -> IngestionResult:
    if not _ingestion_lock.acquire(blocking=False):
        now = _now_iso()
        logger.warning("Ingestion already in progress; skipping overlapping trigger")
        return IngestionResult(
            started_at=now,
            finished_at=now,
            success=False,
            fetch_successes=0,
            fetch_failures=0,
            error="skipped: overlapping run",
        )

    started_at = _now_iso()
    logger.info("Ingestion run started at %s (%s)", started_at, TIMEZONE)

    fetch_successes = 0
    fetch_failures = 0

    try:
        fetch_results = fetch_all()
        fetch_successes = sum(1 for result in fetch_results if result.success)
        fetch_failures = sum(1 for result in fetch_results if not result.success)

        for result in fetch_results:
            if not result.success:
                logger.error(
                    "Fetch failed for %s: %s",
                    result.entry.source_url,
                    result.error,
                )

        logger.info(
            "Fetch step complete: %s succeeded, %s failed",
            fetch_successes,
            fetch_failures,
        )

        index_summary = build_index()
        ingested_at = index_summary["ingested_at"]
        chunk_count = index_summary["chunk_count"]

        finished_at = _now_iso()
        logger.info(
            "Ingestion run succeeded at %s; ingested_at=%s, chunks=%s",
            finished_at,
            ingested_at,
            chunk_count,
        )

        return IngestionResult(
            started_at=started_at,
            finished_at=finished_at,
            success=True,
            fetch_successes=fetch_successes,
            fetch_failures=fetch_failures,
            ingested_at=ingested_at,
            chunk_count=chunk_count,
        )
    except Exception as exc:
        finished_at = _now_iso()
        logger.exception("Ingestion run failed at %s", finished_at)
        return IngestionResult(
            started_at=started_at,
            finished_at=finished_at,
            success=False,
            fetch_successes=fetch_successes,
            fetch_failures=fetch_failures,
            error=str(exc),
        )
    finally:
        _ingestion_lock.release()


def create_scheduler(*, interval_minutes: int | None = None) -> BlockingScheduler:
    """Build APScheduler with IST cron or a dev interval trigger."""
    tz = pytz.timezone(TIMEZONE)
    scheduler = BlockingScheduler(timezone=tz)

    if interval_minutes is not None:
        trigger = IntervalTrigger(minutes=interval_minutes, timezone=tz)
        logger.info("Scheduler using dev interval: every %s minutes", interval_minutes)
    else:
        trigger = CronTrigger(
            hour=INGESTION_CRON_HOURS,
            minute=INGESTION_CRON_MINUTE,
            timezone=tz,
        )
        logger.info(
            "Scheduler using production cron: minute %s at hours %s %s",
            INGESTION_CRON_MINUTE,
            INGESTION_CRON_HOURS,
            TIMEZONE,
        )

    scheduler.add_job(
        run_ingestion,
        trigger,
        id=JOB_ID,
        max_instances=1,
        coalesce=True,
        replace_existing=True,
    )
    return scheduler


def run_daemon(*, interval_minutes: int | None = None) -> None:
    """Start the blocking scheduler process."""
    scheduler = create_scheduler(interval_minutes=interval_minutes)
    logger.info("Starting ingestion scheduler daemon (timezone=%s)", TIMEZONE)
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Scheduler stopped")


def _now_iso() -> str:
    return datetime.now(pytz.timezone(TIMEZONE)).isoformat()


def _configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Scheduled corpus fetch and index rebuild (8x/day IST).",
    )
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument(
        "--once",
        action="store_true",
        help="Run a single ingestion cycle and exit.",
    )
    mode.add_argument(
        "--daemon",
        action="store_true",
        help="Run the APScheduler daemon (09:15 IST + every 3 hours).",
    )
    parser.add_argument(
        "--interval-minutes",
        type=int,
        metavar="N",
        help="Dev mode: fire every N minutes instead of production cron (with --daemon).",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    """CLI entry point: ``--once`` for manual run, ``--daemon`` for scheduler."""
    _configure_logging()
    args = parse_args(argv)

    if args.once:
        result = run_ingestion()
        if not result.success:
            raise SystemExit(1)
        return

    if args.daemon:
        if args.interval_minutes is not None and args.interval_minutes <= 0:
            logger.error("--interval-minutes must be a positive integer")
            raise SystemExit(1)
        run_daemon(interval_minutes=args.interval_minutes)


if __name__ == "__main__":
    main()
