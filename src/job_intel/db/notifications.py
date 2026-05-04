from __future__ import annotations

import sqlite3

from job_intel.core.models import MatchResult


def filter_unsent_telegram_matches(
    conn: sqlite3.Connection,
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
        exists = conn.execute(
            """
            SELECT 1
            FROM telegram_sent_jobs
            WHERE source = ? AND external_id = ? AND chat_id = ?
            LIMIT 1
            """,
            (item.source, item.external_id, chat_id),
        ).fetchone()
        if exists is None:
            unsent.append(item)
        if len(unsent) >= limit:
            break
    return unsent


def record_telegram_sent_jobs(
    conn: sqlite3.Connection,
    results: list[MatchResult],
    *,
    chat_id: str,
) -> None:
    conn.executemany(
        """
        INSERT INTO telegram_sent_jobs (source, external_id, chat_id)
        VALUES (?, ?, ?)
        ON CONFLICT(source, external_id, chat_id) DO UPDATE SET
            last_sent_at = CURRENT_TIMESTAMP,
            send_count = send_count + 1
        """,
        [
            (item.source, item.external_id, chat_id)
            for item in results
            if item.source and item.external_id
        ],
    )
    conn.commit()
