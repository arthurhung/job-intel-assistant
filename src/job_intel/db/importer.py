from __future__ import annotations

import csv
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.dialects.sqlite import insert
from sqlalchemy.orm import Session

from job_intel.core.models import JobPosting
from job_intel.db.models import JobRecord


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


def upsert_jobs(conn: Session, jobs: list[JobPosting]) -> int:
    for job in jobs:
        values = {
            "source": job.source,
            "external_id": job.external_id,
            "title": job.title,
            "company": job.company,
            "location": job.location,
            "url": job.url,
            "description": job.description,
            "salary": job.salary,
            "posted_at": job.posted_at,
        }
        statement = insert(JobRecord).values(**values)
        conn.execute(
            statement.on_conflict_do_update(
                index_elements=["source", "external_id"],
                set_={
                    **values,
                    "updated_at": text("CURRENT_TIMESTAMP"),
                },
            )
        )
    conn.commit()
    return len(jobs)
