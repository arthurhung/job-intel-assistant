from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from job_intel.config import get_settings
from job_intel.crawlers import crawl_jobs
from job_intel.db import session
from job_intel.db.history import record_match_run
from job_intel.db.importer import upsert_jobs
from job_intel.core.job_filters import filter_taiwan_or_remote_jobs
from job_intel.core.matcher import match_jobs
from job_intel.pipeline.report import write_markdown_report
from job_intel.core.resume import load_resume_text
from job_intel.notifications.telegram import send_match_digest


@dataclass(frozen=True)
class PipelineResult:
    crawled_count: int
    imported_count: int
    total_matches: int
    qualified_matches: int
    notified_count: int | None
    match_run_id: int
    report_path: Path


def run_pipeline(
    *,
    source: str,
    resume_path: Path,
    db_path: Path,
    report_path: Path,
    notify_telegram: bool = False,
    telegram_min_score: float = 70.0,
    telegram_limit: int = 5,
) -> PipelineResult:
    settings = get_settings()
    jobs = filter_taiwan_or_remote_jobs(
        crawl_jobs(source),
        allowed_location_keywords=settings.allowed_location_keywords or None,
    )
    resume_text = load_resume_text(resume_path)

    with session(db_path) as conn:
        imported_count = upsert_jobs(conn, jobs)
        results = match_jobs(
            conn,
            resume_text,
            allowed_location_keywords=settings.allowed_location_keywords or None,
        )

    write_markdown_report(results, report_path)

    notified_count: int | None = None
    if notify_telegram:
        notified_count = send_match_digest(
            results,
            db_path=db_path,
            min_score=telegram_min_score,
            limit=telegram_limit,
        )

    with session(db_path) as conn:
        match_run_id = record_match_run(
            conn,
            resume_text=resume_text,
            results=results,
            min_score=telegram_min_score,
            notified_count=notified_count,
        )

    qualified_matches = sum(1 for item in results if item.score >= telegram_min_score)
    return PipelineResult(
        crawled_count=len(jobs),
        imported_count=imported_count,
        total_matches=len(results),
        qualified_matches=qualified_matches,
        notified_count=notified_count,
        match_run_id=match_run_id,
        report_path=report_path,
    )
