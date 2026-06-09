"""Persistent audit log for scheduled and manual ingestion runs."""

from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from src.config import INGESTION_LOG_PATH, TIMEZONE

logger = logging.getLogger(__name__)

SCHEMA_VERSION = "1.0"
MAX_RUNS = 500


@dataclass
class IngestionLogEntry:
    """Single ingestion run record."""

    started_at: str
    finished_at: str
    success: bool
    fetch_successes: int
    fetch_failures: int
    ingested_at: str | None = None
    chunk_count: int | None = None
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _empty_log() -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "description": (
            "Audit trail of corpus fetch and index rebuild runs. "
            "Appended by src.scheduler.jobs on every manual or scheduled ingestion."
        ),
        "timezone": TIMEZONE,
        "runs": [],
    }


def load_ingestion_log(path: Path = INGESTION_LOG_PATH) -> dict[str, Any]:
    """Load the ingestion log, or return an empty structure if missing."""
    if not path.is_file():
        return _empty_log()
    with path.open(encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload.get("runs"), list):
        payload["runs"] = []
    return payload


def append_ingestion_run(
    entry: IngestionLogEntry,
    *,
    path: Path = INGESTION_LOG_PATH,
    max_runs: int = MAX_RUNS,
) -> dict[str, Any]:
    """Append a run record and atomically write the log file."""
    payload = load_ingestion_log(path)
    runs: list[dict[str, Any]] = payload.setdefault("runs", [])
    runs.append(entry.to_dict())
    if len(runs) > max_runs:
        payload["runs"] = runs[-max_runs:]

    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_suffix(".json.tmp")
    with temp_path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)
        handle.write("\n")
    temp_path.replace(path)

    logger.info(
        "Ingestion log updated: success=%s fetch_ok=%s fetch_fail=%s -> %s",
        entry.success,
        entry.fetch_successes,
        entry.fetch_failures,
        path,
    )
    return payload


def latest_ingestion_run(path: Path = INGESTION_LOG_PATH) -> dict[str, Any] | None:
    """Return the most recent run entry, if any."""
    runs = load_ingestion_log(path).get("runs", [])
    if not runs:
        return None
    last = runs[-1]
    return last if isinstance(last, dict) else None


def recent_ingestion_runs(
    *,
    limit: int = 10,
    path: Path = INGESTION_LOG_PATH,
) -> list[dict[str, Any]]:
    """Return the last N run entries (newest last)."""
    runs = load_ingestion_log(path).get("runs", [])
    if limit <= 0:
        return []
    return runs[-limit:]
