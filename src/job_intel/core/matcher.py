from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from job_intel.core.job_filters import is_taiwan_or_remote_job
from job_intel.core.models import MatchResult
from job_intel.core.skills import extract_skills
from job_intel.db.models import JobRecord


def match_jobs(conn: Session, resume_text: str) -> list[MatchResult]:
    resume_skills = set(extract_skills(resume_text))
    results: list[MatchResult] = []

    rows = conn.scalars(select(JobRecord).order_by(JobRecord.posted_at.desc(), JobRecord.updated_at.desc())).all()

    for row in rows:
        if not is_taiwan_or_remote_job(
            source=row.source,
            location=row.location,
            description=row.description,
            title=row.title,
        ):
            continue
        job_skills = set(extract_skills(row.description + " " + row.title))
        matched = sorted(job_skills & resume_skills)
        missing = sorted(job_skills - resume_skills)
        score = (len(matched) / len(job_skills) * 100) if job_skills else 0.0
        results.append(
            MatchResult(
                source=row.source,
                external_id=row.external_id,
                title=row.title,
                company=row.company,
                location=row.location,
                url=row.url,
                score=round(score, 1),
                matched_skills=matched,
                missing_skills=missing,
                summary=_summary(row.description),
            )
        )

    return sorted(results, key=lambda item: item.score, reverse=True)


def _summary(text: str, limit: int = 180) -> str:
    compact = " ".join(text.split())
    if len(compact) <= limit:
        return compact
    return compact[: limit - 3].rstrip() + "..."
