from __future__ import annotations

from pathlib import Path

from sqlalchemy import select

from job_intel.core.models import MatchResult
from job_intel.db import session
from job_intel.db.feedback import record_job_feedback
from job_intel.db.models import TelegramSentJobRecord
from job_intel.db.notifications import filter_unsent_telegram_matches, record_telegram_sent_jobs


def _match(source: str, external_id: str, score: float) -> MatchResult:
    return MatchResult(
        source=source,
        external_id=external_id,
        title="Backend Engineer",
        company="Example Co.",
        location="Taipei",
        url="https://example.com",
        score=score,
        matched_skills=["python"],
        missing_skills=[],
        summary="Build APIs.",
    )


def test_filter_unsent_telegram_matches_respects_threshold_limit_sent_and_feedback(tmp_path: Path) -> None:
    db_path = tmp_path / "notifications.sqlite3"
    results = [
        _match("104", "sent", 95),
        _match("104", "ignored", 92),
        _match("104", "fresh-1", 90),
        _match("104", "fresh-2", 85),
        _match("104", "low", 60),
        _match("", "missing-source", 99),
    ]

    with session(db_path) as conn:
        record_telegram_sent_jobs(conn, [results[0]], chat_id="chat-1")
        record_job_feedback(conn, source="104", external_id="ignored", chat_id="chat-1", feedback="ignored")

        selected = filter_unsent_telegram_matches(conn, results, chat_id="chat-1", min_score=70, limit=1)

    assert [item.external_id for item in selected] == ["fresh-1"]


def test_record_telegram_sent_jobs_upserts_send_count(tmp_path: Path) -> None:
    db_path = tmp_path / "sent.sqlite3"
    result = _match("104", "abc", 90)

    with session(db_path) as conn:
        record_telegram_sent_jobs(conn, [result], chat_id="chat-1")
        record_telegram_sent_jobs(conn, [result], chat_id="chat-1")
        row = conn.scalar(select(TelegramSentJobRecord).where(TelegramSentJobRecord.external_id == "abc"))

    assert row is not None
    assert row.send_count == 2
