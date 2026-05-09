from __future__ import annotations

from pathlib import Path

import pytest

from job_intel.db import session
from job_intel.db.feedback import (
    get_job_feedback,
    is_excluded_by_feedback,
    list_job_feedback,
    record_job_feedback,
)


def test_record_job_feedback_upserts_and_lists_by_chat(tmp_path: Path) -> None:
    db_path = tmp_path / "feedback.sqlite3"

    with session(db_path) as conn:
        record_job_feedback(conn, source="104", external_id="abc", chat_id="chat-1", feedback="interested")
        assert get_job_feedback(conn, source="104", external_id="abc", chat_id="chat-1") == "interested"
        assert not is_excluded_by_feedback(conn, source="104", external_id="abc", chat_id="chat-1")

        record_job_feedback(conn, source="104", external_id="abc", chat_id="chat-1", feedback="applied")

        feedback_by_job = list_job_feedback(conn, chat_id="chat-1")
        assert is_excluded_by_feedback(conn, source="104", external_id="abc", chat_id="chat-1")

    assert feedback_by_job[("104", "abc")].feedback == "applied"


def test_record_job_feedback_rejects_unknown_feedback(tmp_path: Path) -> None:
    db_path = tmp_path / "feedback.sqlite3"

    with session(db_path) as conn:
        with pytest.raises(ValueError, match="Unsupported feedback"):
            record_job_feedback(conn, source="104", external_id="abc", chat_id="chat-1", feedback="maybe")
