from __future__ import annotations

from sqlalchemy import select, text
from sqlalchemy.dialects.sqlite import insert
from sqlalchemy.orm import Session

from job_intel.core.models import MatchResult
from job_intel.db.models import TelegramSentJobRecord


def filter_unsent_telegram_matches(
    conn: Session,
    results: list[MatchResult],
    *,
    chat_id: str,
    min_score: float,
    limit: int,
) -> list[MatchResult]:
    selected = [item for item in results if item.score >= min_score]
    unsent: list[MatchResult] = []
    for item in selected:
        if not item.source or not item.external_id:
            continue
        exists = conn.scalar(
            select(TelegramSentJobRecord.id)
            .where(
                TelegramSentJobRecord.source == item.source,
                TelegramSentJobRecord.external_id == item.external_id,
                TelegramSentJobRecord.chat_id == chat_id,
            )
            .limit(1)
        )
        if exists is None:
            unsent.append(item)
        if len(unsent) >= limit:
            break
    return unsent


def record_telegram_sent_jobs(
    conn: Session,
    results: list[MatchResult],
    *,
    chat_id: str,
) -> None:
    for item in results:
        if not item.source or not item.external_id:
            continue
        statement = insert(TelegramSentJobRecord).values(
            source=item.source,
            external_id=item.external_id,
            chat_id=chat_id,
        )
        conn.execute(
            statement.on_conflict_do_update(
                index_elements=["source", "external_id", "chat_id"],
                set_={
                    "last_sent_at": text("CURRENT_TIMESTAMP"),
                    "send_count": TelegramSentJobRecord.send_count + 1,
                },
            )
        )
    conn.commit()
