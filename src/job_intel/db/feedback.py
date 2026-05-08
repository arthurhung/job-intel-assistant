from __future__ import annotations

from sqlalchemy import select, text
from sqlalchemy.dialects.sqlite import insert
from sqlalchemy.orm import Session

from job_intel.db.models import JobFeedbackRecord


EXCLUDED_FEEDBACK = {"ignored", "applied"}
VALID_FEEDBACK = {"interested", "ignored", "applied"}


def record_job_feedback(
    conn: Session,
    *,
    source: str,
    external_id: str,
    chat_id: str,
    feedback: str,
) -> None:
    if feedback not in VALID_FEEDBACK:
        raise ValueError(f"Unsupported feedback: {feedback}")

    statement = insert(JobFeedbackRecord).values(
        source=source,
        external_id=external_id,
        chat_id=chat_id,
        feedback=feedback,
    )
    conn.execute(
        statement.on_conflict_do_update(
            index_elements=["source", "external_id", "chat_id"],
            set_={
                "feedback": feedback,
                "updated_at": text("CURRENT_TIMESTAMP"),
            },
        )
    )
    conn.commit()


def get_job_feedback(conn: Session, *, source: str, external_id: str, chat_id: str) -> str | None:
    return conn.scalar(
        select(JobFeedbackRecord.feedback)
        .where(
            JobFeedbackRecord.source == source,
            JobFeedbackRecord.external_id == external_id,
            JobFeedbackRecord.chat_id == chat_id,
        )
        .limit(1)
    )


def list_job_feedback(conn: Session, *, chat_id: str) -> dict[tuple[str, str], JobFeedbackRecord]:
    rows = conn.scalars(
        select(JobFeedbackRecord).where(JobFeedbackRecord.chat_id == chat_id)
    ).all()
    return {(row.source, row.external_id): row for row in rows}


def is_excluded_by_feedback(conn: Session, *, source: str, external_id: str, chat_id: str) -> bool:
    feedback = get_job_feedback(conn, source=source, external_id=external_id, chat_id=chat_id)
    return feedback in EXCLUDED_FEEDBACK
