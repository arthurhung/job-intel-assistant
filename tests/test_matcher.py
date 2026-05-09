from __future__ import annotations

from pathlib import Path

from job_intel.core.matcher import match_jobs
from job_intel.core.models import JobPosting
from job_intel.db import session
from job_intel.db.importer import upsert_jobs


def test_match_jobs_scores_skill_overlap_and_keeps_taiwan_jobs(tmp_path: Path) -> None:
    db_path = tmp_path / "matches.sqlite3"
    resume = "Python backend engineer with Airflow, Docker, PostgreSQL, Redis, SQL, and AWS experience."
    jobs = [
        JobPosting(
            source="104",
            external_id="tw-1",
            title="Python Backend Engineer",
            company="Taiwan Co.",
            location="台北市",
            url="https://example.com/tw-1",
            description="Build Python APIs with Docker, PostgreSQL, Redis, SQL, and AWS.",
            salary="",
            posted_at="2026-05-10",
        ),
        JobPosting(
            source="remoteok",
            external_id="remote-1",
            title="Data Engineer",
            company="Remote Co.",
            location="Remote",
            url="https://example.com/remote-1",
            description="Python SQL ETL pipelines.",
            salary="",
            posted_at="2026-05-09",
        ),
        JobPosting(
            source="remoteok",
            external_id="foreign-1",
            title="Backend Engineer",
            company="Foreign Co.",
            location="United States",
            url="https://example.com/foreign-1",
            description="Python SQL backend role requiring US work authorization.",
            salary="",
            posted_at="2026-05-08",
        ),
    ]

    with session(db_path) as conn:
        upsert_jobs(conn, jobs)
        results = match_jobs(conn, resume, allowed_location_keywords=("taipei", "台北", "remote"))

    assert [item.external_id for item in results] == ["tw-1", "remote-1"]
    assert results[0].score > results[1].score
    assert "python" in results[0].matched_skills
