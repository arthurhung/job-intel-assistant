from __future__ import annotations

import tempfile
from dataclasses import asdict
from pathlib import Path

from sqlalchemy import select

from job_intel.crawlers import available_crawlers, crawl_jobs
from job_intel.db import session
from job_intel.db.history import record_match_run
from job_intel.db.importer import upsert_jobs
from job_intel.db.models import JobRecord, MatchRunRecord
from job_intel.core.job_filters import filter_taiwan_or_remote_jobs, is_taiwan_or_remote_job
from job_intel.core.matcher import match_jobs
from job_intel.core.models import MatchResult
from job_intel.core.resume import load_resume_text
from job_intel.llm import analyze_matches_with_llm
from job_intel.notifications.telegram import send_match_digest


SUPPORTED_RESUME_SUFFIXES = {".pdf", ".txt"}


def list_jobs(
    db_path: Path,
    *,
    min_posted_at: str | None = None,
    allowed_location_keywords: tuple[str, ...] = (),
) -> list[dict]:
    with session(db_path) as conn:
        query = select(JobRecord)
        if min_posted_at:
            query = query.where(JobRecord.posted_at >= min_posted_at)
        query = query.order_by(JobRecord.posted_at.desc(), JobRecord.updated_at.desc())
        return [
            serialize_job(row)
            for row in conn.scalars(query).all()
            if is_taiwan_or_remote_job(
                source=row.source,
                location=row.location,
                description=row.description,
                title=row.title,
                allowed_location_keywords=allowed_location_keywords or None,
            )
        ]


def parse_resume_bytes(*, filename: str, body: bytes) -> dict:
    if not body:
        raise ValueError("Resume file is empty.")

    suffix = Path(filename).suffix.lower()
    if suffix not in SUPPORTED_RESUME_SUFFIXES:
        raise ValueError("Only .pdf and .txt resumes are supported.")

    try:
        if suffix == ".txt":
            text = body.decode("utf-8-sig")
        else:
            with tempfile.TemporaryDirectory() as directory:
                resume_path = Path(directory) / f"resume{suffix}"
                resume_path.write_bytes(body)
                text = load_resume_text(resume_path)
    except UnicodeDecodeError as exc:
        raise ValueError("TXT resume must be UTF-8 encoded.") from exc

    text = text.strip()
    if not text:
        raise ValueError("No text could be extracted from this resume.")

    return {"filename": filename, "text": text, "char_count": len(text)}


def run_crawler(db_path: Path, *, source: str, allowed_location_keywords: tuple[str, ...] = ()) -> dict:
    from job_intel.config import get_settings

    settings = get_settings()
    crawled_jobs = crawl_jobs(source, limit_per_source=settings.crawler_limit_per_source)
    jobs = filter_taiwan_or_remote_jobs(
        crawled_jobs,
        allowed_location_keywords=allowed_location_keywords or None,
    )
    with session(db_path) as conn:
        imported_count = upsert_jobs(conn, jobs)
    return {
        "source": source,
        "crawled_count": len(crawled_jobs),
        "imported_count": imported_count,
        "filtered_count": len(crawled_jobs) - len(jobs),
        "available_sources": available_crawlers(),
    }


def create_match_run(
    db_path: Path,
    *,
    resume_text: str,
    use_llm_analysis: bool,
    notify_telegram: bool,
    telegram_min_score: float,
    telegram_limit: int,
    allowed_location_keywords: tuple[str, ...] = (),
) -> dict:
    with session(db_path) as conn:
        results = match_jobs(
            conn,
            resume_text,
            allowed_location_keywords=allowed_location_keywords or None,
        )
    results = analyze_matches_with_llm(
        results,
        resume_text=resume_text,
        enabled=use_llm_analysis,
    )

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

    return {
        "matches": [serialize_match(item) for item in results],
        "notified_count": notified_count,
        "match_run_id": match_run_id,
    }


def list_match_runs(db_path: Path, *, limit: int = 8) -> list[dict]:
    with session(db_path) as conn:
        rows = conn.scalars(
            select(MatchRunRecord)
            .order_by(MatchRunRecord.created_at.desc(), MatchRunRecord.id.desc())
            .limit(limit)
        ).all()
        return [serialize_match_run(row) for row in rows]


def serialize_match(item: MatchResult) -> dict:
    return asdict(item)


def serialize_job(row: JobRecord) -> dict:
    return {
        "id": row.id,
        "source": row.source,
        "external_id": row.external_id,
        "title": row.title,
        "company": row.company,
        "location": row.location,
        "url": row.url,
        "description": row.description,
        "salary": row.salary,
        "posted_at": row.posted_at,
        "updated_at": row.updated_at,
    }


def serialize_match_run(row: MatchRunRecord) -> dict:
    return {
        "id": row.id,
        "resume_preview": row.resume_preview,
        "resume_chars": row.resume_chars,
        "min_score": row.min_score,
        "total_matches": row.total_matches,
        "qualified_matches": row.qualified_matches,
        "notified_count": row.notified_count,
        "created_at": row.created_at,
    }
