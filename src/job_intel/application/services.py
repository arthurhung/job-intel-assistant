from __future__ import annotations

import tempfile
from dataclasses import asdict
from pathlib import Path

from job_intel.crawlers import available_crawlers, crawl_jobs
from job_intel.db import session
from job_intel.db.history import record_match_run
from job_intel.db.importer import upsert_jobs
from job_intel.core.job_filters import filter_taiwan_or_remote_jobs, is_taiwan_or_remote_job
from job_intel.core.matcher import match_jobs
from job_intel.core.models import MatchResult
from job_intel.core.resume import load_resume_text
from job_intel.notifications.telegram import send_match_digest


SUPPORTED_RESUME_SUFFIXES = {".pdf", ".txt"}


def list_jobs(db_path: Path, *, min_posted_at: str | None = None) -> list[dict]:
    with session(db_path) as conn:
        query = """
            SELECT id, source, external_id, title, company, location, url,
                   description, salary, posted_at, updated_at
            FROM jobs
        """
        params: list[str] = []
        if min_posted_at:
            query += " WHERE posted_at >= ?"
            params.append(min_posted_at)
        query += " ORDER BY posted_at DESC, updated_at DESC"
        return [
            dict(row)
            for row in conn.execute(query, params).fetchall()
            if is_taiwan_or_remote_job(
                source=row["source"],
                location=row["location"],
                description=row["description"],
                title=row["title"],
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


def run_crawler(db_path: Path, *, source: str) -> dict:
    crawled_jobs = crawl_jobs(source)
    jobs = filter_taiwan_or_remote_jobs(crawled_jobs)
    with session(db_path) as conn:
        imported_count = upsert_jobs(conn, jobs)
    return {
        "source": source,
        "imported_count": imported_count,
        "filtered_count": len(crawled_jobs) - len(jobs),
        "available_sources": available_crawlers(),
    }


def create_match_run(
    db_path: Path,
    *,
    resume_text: str,
    notify_telegram: bool,
    telegram_min_score: float,
    telegram_limit: int,
) -> dict:
    with session(db_path) as conn:
        results = match_jobs(conn, resume_text)

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
        rows = conn.execute(
            """
            SELECT id, resume_preview, resume_chars, min_score, total_matches,
                   qualified_matches, notified_count, created_at
            FROM match_runs
            ORDER BY created_at DESC, id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
        return [dict(row) for row in rows]


def serialize_match(item: MatchResult) -> dict:
    return asdict(item)
