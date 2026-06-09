"""Unit tests for the ingestion scheduler."""

from __future__ import annotations

import threading
from unittest.mock import MagicMock, patch

import pytest
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from src.scheduler.jobs import (
    INGESTION_CRON_HOURS,
    INGESTION_CRON_MINUTE,
    JOB_ID,
    create_scheduler,
    run_ingestion,
)


@patch("src.scheduler.jobs.append_ingestion_run")
@patch("src.scheduler.jobs.build_index")
@patch("src.scheduler.jobs.fetch_all")
def test_run_ingestion_success(mock_fetch, mock_build, mock_append) -> None:
    mock_fetch.return_value = [MagicMock(success=True), MagicMock(success=True)]
    mock_build.return_value = {
        "ingested_at": "2026-06-08T07:27:03.556464+00:00",
        "chunk_count": 55,
    }

    result = run_ingestion()

    assert result.success
    assert result.fetch_successes == 2
    assert result.fetch_failures == 0
    assert result.ingested_at == "2026-06-08T07:27:03.556464+00:00"
    assert result.chunk_count == 55
    mock_fetch.assert_called_once_with()
    mock_build.assert_called_once_with()
    mock_append.assert_called_once()


@patch("src.scheduler.jobs.append_ingestion_run")
@patch("src.scheduler.jobs.build_index")
@patch("src.scheduler.jobs.fetch_all")
def test_run_ingestion_continues_after_fetch_failures(mock_fetch, mock_build, mock_append) -> None:
    failed = MagicMock(
        success=False,
        entry=MagicMock(source_url="https://groww.in/example"),
        error="timeout",
    )
    mock_fetch.return_value = [failed, MagicMock(success=True)]
    mock_build.return_value = {
        "ingested_at": "2026-06-08T07:27:03.556464+00:00",
        "chunk_count": 55,
    }

    result = run_ingestion()

    assert result.success
    assert result.fetch_failures == 1
    assert result.fetch_successes == 1
    mock_build.assert_called_once_with()
    mock_append.assert_called_once()


@patch("src.scheduler.jobs.append_ingestion_run")
@patch("src.scheduler.jobs.build_index")
@patch("src.scheduler.jobs.fetch_all")
def test_run_ingestion_index_failure_preserves_previous_index(
    mock_fetch, mock_build, mock_append
) -> None:
    mock_fetch.return_value = [MagicMock(success=True)]
    mock_build.side_effect = RuntimeError("embed failed")

    result = run_ingestion()

    assert not result.success
    assert result.error == "embed failed"
    assert result.ingested_at is None
    mock_append.assert_called_once()


@patch("src.scheduler.jobs.append_ingestion_run")
@patch("src.scheduler.jobs.build_index")
@patch("src.scheduler.jobs.fetch_all")
def test_run_ingestion_skips_overlapping_run(mock_fetch, mock_build, mock_append) -> None:
    lock = threading.Lock()
    lock.acquire()
    try:
        with patch("src.scheduler.jobs._ingestion_lock", lock):
            result = run_ingestion()
    finally:
        lock.release()

    assert not result.success
    assert result.error == "skipped: overlapping run"
    mock_fetch.assert_not_called()
    mock_build.assert_not_called()
    mock_append.assert_called_once()


def test_create_scheduler_production_cron() -> None:
    scheduler = create_scheduler()
    job = scheduler.get_job(JOB_ID)

    assert job is not None
    assert job.max_instances == 1
    assert isinstance(job.trigger, CronTrigger)
    assert str(job.trigger.fields[5]) == INGESTION_CRON_HOURS
    assert str(job.trigger.fields[6]) == str(INGESTION_CRON_MINUTE)


def test_create_scheduler_dev_interval() -> None:
    scheduler = create_scheduler(interval_minutes=5)
    job = scheduler.get_job(JOB_ID)

    assert job is not None
    assert isinstance(job.trigger, IntervalTrigger)
    assert job.trigger.interval.total_seconds() == 300


def test_cli_once_exits_on_failure() -> None:
    from src.scheduler import jobs

    with patch.object(jobs, "run_ingestion", return_value=MagicMock(success=False)):
        with pytest.raises(SystemExit) as exc_info:
            jobs.main(["--once"])
        assert exc_info.value.code == 1


def test_cli_once_succeeds() -> None:
    from src.scheduler import jobs

    with patch.object(jobs, "run_ingestion", return_value=MagicMock(success=True)):
        jobs.main(["--once"])


def test_cli_daemon_rejects_invalid_interval() -> None:
    from src.scheduler import jobs

    with pytest.raises(SystemExit) as exc_info:
        jobs.main(["--daemon", "--interval-minutes", "0"])
    assert exc_info.value.code == 1


def test_append_ingestion_run_creates_log(tmp_path) -> None:
    from src.scheduler.ingestion_log import (
        IngestionLogEntry,
        append_ingestion_run,
        latest_ingestion_run,
        load_ingestion_log,
    )

    log_path = tmp_path / "ingestion_log.json"
    entry = IngestionLogEntry(
        started_at="2026-06-09T09:15:00+05:30",
        finished_at="2026-06-09T09:16:00+05:30",
        success=True,
        fetch_successes=12,
        fetch_failures=0,
        ingested_at="2026-06-09T03:46:00+00:00",
        chunk_count=55,
    )

    append_ingestion_run(entry, path=log_path)

    payload = load_ingestion_log(log_path)
    assert payload["schema_version"] == "1.0"
    assert len(payload["runs"]) == 1
    latest = latest_ingestion_run(log_path)
    assert latest is not None
    assert latest["success"] is True
    assert latest["fetch_successes"] == 12
    assert latest["chunk_count"] == 55


def test_append_ingestion_run_trims_old_entries(tmp_path) -> None:
    from src.scheduler.ingestion_log import IngestionLogEntry, append_ingestion_run, load_ingestion_log

    log_path = tmp_path / "ingestion_log.json"
    for index in range(5):
        append_ingestion_run(
            IngestionLogEntry(
                started_at=f"2026-06-09T09:{index:02d}:00+05:30",
                finished_at=f"2026-06-09T09:{index:02d}:30+05:30",
                success=True,
                fetch_successes=12,
                fetch_failures=0,
            ),
            path=log_path,
            max_runs=3,
        )

    runs = load_ingestion_log(log_path)["runs"]
    assert len(runs) == 3
    assert runs[0]["started_at"].endswith("02:00+05:30")
    assert runs[-1]["started_at"].endswith("04:00+05:30")
