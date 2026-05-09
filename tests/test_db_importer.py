from __future__ import annotations

from pathlib import Path

from sqlalchemy import select

from job_intel.core.models import JobPosting
from job_intel.db import session
from job_intel.db.importer import upsert_jobs
from job_intel.db.models import JobRecord


def _job(*, title: str, description: str = "Python SQL backend role") -> JobPosting:
    return JobPosting(
        source="unit",
        external_id="job-1",
        title=title,
        company="Example Co.",
        location="Taipei",
        url="https://example.com/job-1",
        description=description,
        salary="",
        posted_at="2026-05-10",
    )


def test_upsert_jobs_deduplicates_by_source_and_external_id(tmp_path: Path) -> None:
    db_path = tmp_path / "jobs.sqlite3"

    with session(db_path) as conn:
        assert upsert_jobs(conn, [_job(title="Backend Engineer")]) == 1
        assert upsert_jobs(conn, [_job(title="Senior Backend Engineer")]) == 1

        rows = conn.scalars(select(JobRecord)).all()

    assert len(rows) == 1
    assert rows[0].title == "Senior Backend Engineer"
