from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from job_intel.core.job_filters import is_taiwan_or_remote_job
from job_intel.core.models import MatchResult
from job_intel.core.skills import extract_skills
from job_intel.db.models import JobRecord


RESUME_SKILL_CAP = 8
SINGLE_SKILL_SCORE_CAP = 55.0
TWO_SKILL_SCORE_CAP = 75.0


def match_jobs(
    conn: Session,
    resume_text: str,
    *,
    allowed_location_keywords: tuple[str, ...] | None = None,
) -> list[MatchResult]:
    resume_skills = set(extract_skills(resume_text))
    results: list[MatchResult] = []

    rows = conn.scalars(select(JobRecord).order_by(JobRecord.posted_at.desc(), JobRecord.updated_at.desc())).all()

    for row in rows:
        if not is_taiwan_or_remote_job(
            source=row.source,
            location=row.location,
            description=row.description,
            title=row.title,
            allowed_location_keywords=allowed_location_keywords,
        ):
            continue
        job_skills = set(extract_skills(row.description + " " + row.title))
        matched = sorted(job_skills & resume_skills)
        missing = sorted(job_skills - resume_skills)
        score = _score_match(matched_count=len(matched), job_skill_count=len(job_skills), resume_skill_count=len(resume_skills))
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


def _score_match(*, matched_count: int, job_skill_count: int, resume_skill_count: int) -> float:
    if matched_count == 0 or job_skill_count == 0 or resume_skill_count == 0:
        return 0.0

    job_coverage = matched_count / job_skill_count
    resume_relevance = matched_count / min(resume_skill_count, RESUME_SKILL_CAP)
    score = (job_coverage * 70) + (resume_relevance * 30)

    if matched_count == 1:
        score = min(score, SINGLE_SKILL_SCORE_CAP)
    elif matched_count == 2:
        score = min(score, TWO_SKILL_SCORE_CAP)

    return min(score, 100.0)


def _summary(text: str, limit: int = 180) -> str:
    compact = " ".join(text.split())
    if len(compact) <= limit:
        return compact
    return compact[: limit - 3].rstrip() + "..."
