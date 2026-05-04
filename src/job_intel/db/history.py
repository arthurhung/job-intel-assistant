from __future__ import annotations

import re
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from job_intel.core.models import MatchResult
from job_intel.db.models import MatchRunRecord


EMAIL_PATTERN = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
PHONE_PATTERN = re.compile(r"(?<!\d)(?:\+?\d[\d\s().-]{7,}\d)(?!\d)")


def record_match_run(
    conn: Session,
    *,
    resume_text: str,
    results: list[MatchResult],
    min_score: float,
    notified_count: int | None,
) -> int:
    compact_resume = " ".join(resume_text.split())
    resume_preview = _redact_resume_preview(compact_resume)[:240]
    qualified_matches = sum(1 for item in results if item.score >= min_score)
    run = MatchRunRecord(
        resume_preview=resume_preview,
        resume_chars=len(resume_text),
        min_score=min_score,
        total_matches=len(results),
        qualified_matches=qualified_matches,
        notified_count=notified_count,
        created_at=datetime.now(UTC).isoformat(timespec="seconds"),
    )
    conn.add(run)
    conn.commit()
    return run.id


def _redact_resume_preview(value: str) -> str:
    without_email = EMAIL_PATTERN.sub("[email redacted]", value)
    return PHONE_PATTERN.sub("[phone redacted]", without_email)
