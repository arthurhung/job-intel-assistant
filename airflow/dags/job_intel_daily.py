from __future__ import annotations

import os
from datetime import datetime, timedelta
from pathlib import Path

from airflow.decorators import dag, task


DEFAULT_ARGS = {
    "owner": "job-intel",
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
}


@dag(
    dag_id="job_intel_daily",
    description="Crawl jobs, match a resume, write a report, and optionally send Telegram notifications.",
    default_args=DEFAULT_ARGS,
    schedule="@daily",
    start_date=datetime(2026, 5, 1),
    catchup=False,
    tags=["jobs", "etl", "telegram"],
)
def job_intel_daily() -> None:
    @task
    def run_job_intel_pipeline() -> dict:
        from job_intel.pipeline import run_pipeline

        resume_path = os.getenv("JOB_INTEL_RESUME_PATH")
        if not resume_path:
            raise ValueError("JOB_INTEL_RESUME_PATH must point to a .pdf or .txt resume.")

        result = run_pipeline(
            source=os.getenv("JOB_INTEL_CRAWLER_SOURCE", "all"),
            resume_path=Path(resume_path),
            db_path=Path(os.getenv("JOB_INTEL_DB_PATH", "data/job_intel.sqlite3")),
            report_path=Path(os.getenv("JOB_INTEL_REPORT_PATH", "reports/match_report.md")),
            notify_telegram=os.getenv("JOB_INTEL_NOTIFY_TELEGRAM", "false").lower() == "true",
            use_llm_analysis=os.getenv("JOB_INTEL_USE_LLM_ANALYSIS", "false").lower() == "true",
            telegram_min_score=float(os.getenv("JOB_INTEL_TELEGRAM_MIN_SCORE", "70")),
            telegram_limit=int(os.getenv("JOB_INTEL_TELEGRAM_LIMIT", "5")),
        )
        return {
            "crawled_count": result.crawled_count,
            "imported_count": result.imported_count,
            "total_matches": result.total_matches,
            "qualified_matches": result.qualified_matches,
            "notified_count": result.notified_count,
            "match_run_id": result.match_run_id,
            "report_path": str(result.report_path),
        }

    run_job_intel_pipeline()


job_intel_daily()
