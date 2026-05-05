from __future__ import annotations

import json
import os
import re
from dataclasses import asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from airflow.decorators import dag, task
from airflow.operators.python import get_current_context


DEFAULT_ARGS = {
    "owner": "job-intel",
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
}


def _env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.lower() in {"1", "true", "yes", "y", "on"}


def _db_path() -> Path:
    return Path(os.getenv("JOB_INTEL_DB_PATH", "data/job_intel.sqlite3"))


def _resume_path() -> Path:
    value = os.getenv("JOB_INTEL_RESUME_PATH")
    if not value:
        raise ValueError("JOB_INTEL_RESUME_PATH must point to a .pdf or .txt resume.")
    return Path(value)


def _report_path() -> Path:
    return Path(os.getenv("JOB_INTEL_REPORT_PATH", "reports/match_report.md"))


def _match_artifact_path() -> Path:
    context = get_current_context()
    run_id = re.sub(r"[^a-zA-Z0-9_.-]+", "_", context["run_id"])
    directory = Path(os.getenv("JOB_INTEL_AIRFLOW_ARTIFACT_DIR", "data/airflow"))
    directory.mkdir(parents=True, exist_ok=True)
    return directory / f"matches_{run_id}.json"


def _write_matches(path: Path, matches: list[Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = [asdict(item) for item in matches]
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _read_matches(path: str | Path) -> list[Any]:
    from job_intel.core.models import MatchResult

    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    return [MatchResult(**item) for item in payload]


@dag(
    dag_id="job_intel_daily",
    description="Crawl jobs, match a resume, write a report, and optionally send Telegram notifications.",
    default_args=DEFAULT_ARGS,
    schedule="@daily",
    start_date=datetime(2026, 5, 1),
    catchup=False,
    tags=["jobs", "etl", "telegram"],
)
def job_intel_daily() -> None:
    @task
    def crawl_and_import_jobs() -> dict:
        from job_intel.config import get_settings
        from job_intel.crawlers import crawl_jobs
        from job_intel.core.job_filters import filter_taiwan_or_remote_jobs
        from job_intel.db import session
        from job_intel.db.importer import upsert_jobs

        settings = get_settings()
        source = os.getenv("JOB_INTEL_CRAWLER_SOURCE", "all")
        crawled_jobs = crawl_jobs(source)
        scoped_jobs = filter_taiwan_or_remote_jobs(
            crawled_jobs,
            allowed_location_keywords=settings.allowed_location_keywords or None,
        )
        with session(_db_path()) as conn:
            imported_count = upsert_jobs(conn, scoped_jobs)

        return {
            "source": source,
            "crawled_count": len(crawled_jobs),
            "imported_count": imported_count,
            "filtered_count": len(crawled_jobs) - len(scoped_jobs),
        }

    @task
    def match_resume(crawl_result: dict) -> dict:
        from job_intel.config import get_settings
        from job_intel.core.matcher import match_jobs
        from job_intel.core.resume import load_resume_text
        from job_intel.db import session
        from job_intel.llm import analyze_matches_with_llm

        settings = get_settings()
        resume_text = load_resume_text(_resume_path())
        with session(_db_path()) as conn:
            matches = match_jobs(
                conn,
                resume_text,
                allowed_location_keywords=settings.allowed_location_keywords or None,
            )
        matches = analyze_matches_with_llm(
            matches,
            resume_text=resume_text,
            enabled=_env_bool("JOB_INTEL_USE_LLM_ANALYSIS"),
        )

        artifact_path = _match_artifact_path()
        _write_matches(artifact_path, matches)
        min_score = float(os.getenv("JOB_INTEL_TELEGRAM_MIN_SCORE", "70"))
        return {
            "artifact_path": str(artifact_path),
            "total_matches": len(matches),
            "qualified_matches": sum(1 for item in matches if item.score >= min_score),
            "min_score": min_score,
            "used_llm_analysis": _env_bool("JOB_INTEL_USE_LLM_ANALYSIS"),
            "upstream_source": crawl_result["source"],
        }

    @task
    def write_match_report(match_result: dict) -> dict:
        from job_intel.pipeline.report import write_markdown_report

        matches = _read_matches(match_result["artifact_path"])
        report_path = _report_path()
        write_markdown_report(matches, report_path)
        return {"report_path": str(report_path)}

    @task
    def send_telegram_digest(match_result: dict) -> dict:
        from job_intel.notifications.telegram import send_match_digest

        if not _env_bool("JOB_INTEL_NOTIFY_TELEGRAM"):
            return {"notified_count": None, "enabled": False}

        matches = _read_matches(match_result["artifact_path"])
        notified_count = send_match_digest(
            matches,
            db_path=_db_path(),
            min_score=float(os.getenv("JOB_INTEL_TELEGRAM_MIN_SCORE", "70")),
            limit=int(os.getenv("JOB_INTEL_TELEGRAM_LIMIT", "5")),
        )
        return {"notified_count": notified_count, "enabled": True}

    @task
    def record_match_history(
        crawl_result: dict,
        match_result: dict,
        report_result: dict,
        telegram_result: dict,
    ) -> dict:
        from job_intel.core.resume import load_resume_text
        from job_intel.db import session
        from job_intel.db.history import record_match_run

        matches = _read_matches(match_result["artifact_path"])
        resume_text = load_resume_text(_resume_path())
        notified_count = telegram_result["notified_count"]
        with session(_db_path()) as conn:
            match_run_id = record_match_run(
                conn,
                resume_text=resume_text,
                results=matches,
                min_score=match_result["min_score"],
                notified_count=notified_count,
            )

        return {
            **crawl_result,
            "total_matches": match_result["total_matches"],
            "qualified_matches": match_result["qualified_matches"],
            "notified_count": notified_count,
            "match_run_id": match_run_id,
            "report_path": report_result["report_path"],
            "used_llm_analysis": match_result["used_llm_analysis"],
        }

    crawl = crawl_and_import_jobs()
    match = match_resume(crawl)
    report = write_match_report(match)
    telegram = send_telegram_digest(match)
    history = record_match_history(crawl, match, report, telegram)

    crawl >> match
    match >> [report, telegram]
    [report, telegram] >> history


job_intel_daily()
