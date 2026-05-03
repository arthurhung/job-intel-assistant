from __future__ import annotations

import sqlite3
import re
from datetime import UTC, datetime

from job_intel.models import MatchResult


EMAIL_PATTERN = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
PHONE_PATTERN = re.compile(r"(?<!\d)(?:\+?\d[\d\s().-]{7,}\d)(?!\d)")


def record_match_run(
    conn: sqlite3.Connection,
    *,
    resume_text: str,
    results: list[MatchResult],
    min_score: float,
    notified_count: int | None,
) -> int:
    compact_resume = " ".join(resume_text.split())
    resume_preview = _redact_resume_preview(compact_resume)[:240]
    qualified_matches = sum(1 for item in results if item.score >= min_score)
    cursor = conn.execute(
        """
        INSERT INTO match_runs (
            resume_preview, resume_chars, min_score, total_matches,
            qualified_matches, notified_count, created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            resume_preview,
            len(resume_text),
            min_score,
            len(results),
            qualified_matches,
            notified_count,
            datetime.now(UTC).isoformat(timespec="seconds"),
        ),
    )
    conn.commit()
    return int(cursor.lastrowid)


def _redact_resume_preview(value: str) -> str:
    without_email = EMAIL_PATTERN.sub("[email redacted]", value)
    return PHONE_PATTERN.sub("[phone redacted]", without_email)
