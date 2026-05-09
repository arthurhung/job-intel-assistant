from __future__ import annotations

from pathlib import Path

from sqlalchemy import select

from job_intel.core.models import MatchResult
from job_intel.db import session
from job_intel.db.history import record_match_run
from job_intel.db.models import MatchRunRecord


def _match(*, score: float) -> MatchResult:
    return MatchResult(
        source="104",
        external_id=f"job-{score}",
        title="Backend Engineer",
        company="Example Co.",
        location="Taipei",
        url="https://example.com",
        score=score,
        matched_skills=["python"],
        missing_skills=[],
        summary="Build APIs.",
    )


def test_record_match_run_counts_matches_and_redacts_preview(tmp_path: Path) -> None:
    db_path = tmp_path / "history.sqlite3"
    resume_text = "Arthur arthur@example.com +886 912 345 678 Python backend engineer"

    with session(db_path) as conn:
        run_id = record_match_run(
            conn,
            resume_text=resume_text,
            results=[_match(score=80), _match(score=60)],
            min_score=70,
            notified_count=1,
        )
        row = conn.scalar(select(MatchRunRecord).where(MatchRunRecord.id == run_id))

    assert row is not None
    assert row.total_matches == 2
    assert row.qualified_matches == 1
    assert row.notified_count == 1
    assert "[email redacted]" in row.resume_preview
    assert "[phone redacted]" in row.resume_preview
