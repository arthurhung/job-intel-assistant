from job_intel.db.connection import connect, session
from job_intel.db.feedback import (
    get_job_feedback,
    is_excluded_by_feedback,
    list_job_feedback,
    record_job_feedback,
)
from job_intel.db.history import record_match_run
from job_intel.db.importer import read_jobs_csv, upsert_jobs
from job_intel.db.notifications import filter_unsent_telegram_matches, record_telegram_sent_jobs

__all__ = [
    "connect",
    "filter_unsent_telegram_matches",
    "get_job_feedback",
    "is_excluded_by_feedback",
    "list_job_feedback",
    "read_jobs_csv",
    "record_job_feedback",
    "record_match_run",
    "record_telegram_sent_jobs",
    "session",
    "upsert_jobs",
]
