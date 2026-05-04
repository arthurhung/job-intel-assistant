from __future__ import annotations

import csv
import sqlite3
from pathlib import Path

from job_intel.core.models import JobPosting


REQUIRED_COLUMNS = {
    "source",
    "external_id",
    "title",
    "company",
    "location",
    "url",
    "description",
    "salary",
    "posted_at",
}


def read_jobs_csv(path: Path) -> list[JobPosting]:
    with path.open("r", encoding="utf-8-sig", newline="") as fp:
        reader = csv.DictReader(fp)
        missing = REQUIRED_COLUMNS - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"Missing CSV columns: {', '.join(sorted(missing))}")
        return [
            JobPosting(
                source=row["source"].strip(),
                external_id=row["external_id"].strip(),
                title=row["title"].strip(),
                company=row["company"].strip(),
                location=row["location"].strip(),
                url=row["url"].strip(),
                description=row["description"].strip(),
                salary=row["salary"].strip(),
                posted_at=row["posted_at"].strip(),
            )
            for row in reader
        ]


def upsert_jobs(conn: sqlite3.Connection, jobs: list[JobPosting]) -> int:
    for job in jobs:
        conn.execute(
            """
            INSERT INTO jobs (
                source, external_id, title, company, location, url,
                description, salary, posted_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(source, external_id) DO UPDATE SET
                title = excluded.title,
                company = excluded.company,
                location = excluded.location,
                url = excluded.url,
                description = excluded.description,
                salary = excluded.salary,
                posted_at = excluded.posted_at,
                updated_at = CURRENT_TIMESTAMP
            """,
            (
                job.source,
                job.external_id,
                job.title,
                job.company,
                job.location,
                job.url,
                job.description,
                job.salary,
                job.posted_at,
            ),
        )
    conn.commit()
    return len(jobs)
