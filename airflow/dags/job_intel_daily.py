from __future__ import annotations

import json
import os
import re
import pprint
from dataclasses import asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from airflow.decorators import dag, task
from airflow.operators.python import get_current_context


DEFAULT_ARGS = {
    "owner": "job-intel",
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
}


def _env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.lower() in {"1", "true", "yes", "y", "on"}


def _db_path() -> Path:
    return Path(os.getenv("JOB_INTEL_DB_PATH", "data/job_intel.sqlite3"))


def _resume_path() -> Path:
    value = os.getenv("JOB_INTEL_RESUME_PATH")
    if not value:
        raise ValueError("JOB_INTEL_RESUME_PATH must point to a .pdf or .txt resume.")
    return Path(value)


def _report_path() -> Path:
    return Path(os.getenv("JOB_INTEL_REPORT_PATH", "reports/match_report.md"))


def _match_artifact_path(label: str = "matches") -> Path:
    context = get_current_context()
    run_id = re.sub(r"[^a-zA-Z0-9_.-]+", "_", context["run_id"])
    directory = Path(os.getenv("JOB_INTEL_AIRFLOW_ARTIFACT_DIR", "data/airflow"))
    directory.mkdir(parents=True, exist_ok=True)
    safe_label = re.sub(r"[^a-zA-Z0-9_.-]+", "_", label)
    return directory / f"{safe_label}_{run_id}.json"


def _write_matches(path: Path, matches: list[Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = [asdict(item) for item in matches]
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _read_matches(path: str | Path) -> list[Any]:
    from job_intel.core.models import MatchResult

    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    return [MatchResult(**item) for item in payload]


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
    def crawl_and_import_jobs() -> dict:
        from job_intel.config import get_settings
        from job_intel.application.services import run_crawler

        settings = get_settings()
        source = os.getenv("JOB_INTEL_CRAWLER_SOURCE", "all")
        result = run_crawler(
            _db_path(),
            source=source,
            allowed_location_keywords=settings.allowed_location_keywords or None,
        )
        return {
            "source": result["source"],
            "crawled_count": result["crawled_count"],
            "imported_count": result["imported_count"],
            "filtered_count": result["filtered_count"],
            "source_stats": result.get("source_stats", []),
        }

    @task
    def initial_match_resume(crawl_result: dict) -> dict:
        from job_intel.config import get_settings
        from job_intel.core.matcher import match_jobs
        from job_intel.core.resume import load_resume_text
        from job_intel.db import session
        from job_intel.llm import analyze_matches_with_llm

        settings = get_settings()
        resume_text = load_resume_text(_resume_path())
        with session(_db_path()) as conn:
            matches = match_jobs(
                conn,
                resume_text,
                allowed_location_keywords=settings.allowed_location_keywords or None,
            )
        matches = analyze_matches_with_llm(
            matches,
            resume_text=resume_text,
            enabled=False,
        )

        artifact_path = _match_artifact_path("initial_matches")
        _write_matches(artifact_path, matches)
        min_score = float(os.getenv("JOB_INTEL_TELEGRAM_MIN_SCORE", "70"))
        return {
            "artifact_path": str(artifact_path),
            "total_matches": len(matches),
            "qualified_matches": sum(1 for item in matches if item.score >= min_score),
            "min_score": min_score,
            "used_llm_analysis": False,
            "upstream_source": crawl_result["source"],
        }

    @task
    def preview_telegram_candidates(match_result: dict) -> dict:
        from job_intel.db import filter_unsent_telegram_matches, session

        chat_id = os.getenv("TELEGRAM_CHAT_ID", "").strip()
        if not chat_id:
            return {"notified_count": None, "enabled": False, "reason": "TELEGRAM_CHAT_ID is not set."}

        matches = _read_matches(match_result["artifact_path"])
        with session(_db_path()) as conn:
            candidates = filter_unsent_telegram_matches(
                conn,
                matches,
                chat_id=chat_id,
                min_score=match_result["min_score"],
                limit=int(os.getenv("JOB_INTEL_TELEGRAM_LIMIT", "5")),
            )
        return {
            "notified_count": len(candidates),
            "enabled": _env_bool("JOB_INTEL_NOTIFY_TELEGRAM"),
            "reason": "Preview of unsent Telegram candidates before final notification.",
        }

    @task
    def assess_recommendation_quality(match_result: dict, telegram_preview: dict) -> dict:
        from job_intel.agent import assess_recommendation_quality as assess_quality
        from job_intel.agent import keywords_from_resume
        from job_intel.core.resume import load_resume_text

        matches = _read_matches(match_result["artifact_path"])
        resume_text = load_resume_text(_resume_path())
        decision = assess_quality(
            matches,
            min_score=match_result["min_score"],
            notified_count=telegram_preview["notified_count"],
            followup_keywords=keywords_from_resume(resume_text),
        )
        enabled = _env_bool("JOB_INTEL_AGENT_TOOL_LOOP", True)
        data = decision.to_dict()
        if not enabled:
            data["should_followup_crawl_104"] = False
            data["followup_keywords"] = []
            data["effective_min_score"] = match_result["min_score"]
            data["reasons"] = ["Agent tool loop is disabled."]
        print("Agent recommendation quality assessment")
        print(pprint.pformat(data, sort_dicts=False))
        return data

    @task
    def run_agent_tool_loop(agent_decision: dict) -> dict:
        from job_intel.agent import AgentDecision, RecommendationQuality, run_agent_followup_crawl
        from job_intel.config import get_settings

        settings = get_settings()
        quality = RecommendationQuality(**agent_decision["quality"])
        decision = AgentDecision(
            quality=quality,
            should_followup_crawl_104=agent_decision["should_followup_crawl_104"],
            followup_keywords=tuple(agent_decision.get("followup_keywords", [])),
            effective_min_score=agent_decision["effective_min_score"],
            reasons=tuple(agent_decision.get("reasons", [])),
        )
        result = run_agent_followup_crawl(
            db_path=_db_path(),
            allowed_location_keywords=settings.allowed_location_keywords or None,
            decision=decision,
            limit=int(os.getenv("JOB_INTEL_AGENT_104_LIMIT", "25")),
        )
        print("Agent tool-loop action")
        print(pprint.pformat(result, sort_dicts=False))
        return result

    @task
    def final_match_resume(agent_decision: dict, agent_action: dict) -> dict:
        from job_intel.config import get_settings
        from job_intel.core.matcher import match_jobs
        from job_intel.core.resume import load_resume_text
        from job_intel.db import session
        from job_intel.llm import analyze_matches_with_llm

        settings = get_settings()
        resume_text = load_resume_text(_resume_path())
        with session(_db_path()) as conn:
            matches = match_jobs(
                conn,
                resume_text,
                allowed_location_keywords=settings.allowed_location_keywords or None,
            )
        matches = analyze_matches_with_llm(
            matches,
            resume_text=resume_text,
            enabled=_env_bool("JOB_INTEL_USE_LLM_ANALYSIS"),
        )

        artifact_path = _match_artifact_path("final_matches")
        _write_matches(artifact_path, matches)
        min_score = float(agent_decision["effective_min_score"])
        return {
            "artifact_path": str(artifact_path),
            "total_matches": len(matches),
            "qualified_matches": sum(
                1
                for item in matches
                if (item.llm_score if item.llm_score is not None else item.score) >= min_score
            ),
            "min_score": min_score,
            "used_llm_analysis": _env_bool("JOB_INTEL_USE_LLM_ANALYSIS"),
            "agent_action": agent_action,
            "agent_reasons": agent_decision.get("reasons", []),
        }

    @task
    def write_match_report(match_result: dict) -> dict:
        from job_intel.pipeline.report import write_markdown_report

        matches = _read_matches(match_result["artifact_path"])
        report_path = _report_path()
        write_markdown_report(matches, report_path)
        return {"report_path": str(report_path)}

    @task
    def send_telegram_digest(match_result: dict) -> dict:
        from job_intel.notifications.telegram import send_match_digest

        if not _env_bool("JOB_INTEL_NOTIFY_TELEGRAM"):
            return {"notified_count": None, "enabled": False}

        matches = _read_matches(match_result["artifact_path"])
        notified_count = send_match_digest(
            matches,
            db_path=_db_path(),
            min_score=float(os.getenv("JOB_INTEL_TELEGRAM_MIN_SCORE", "70")),
            limit=int(os.getenv("JOB_INTEL_TELEGRAM_LIMIT", "5")),
        )
        return {"notified_count": notified_count, "enabled": True}

    @task
    def record_match_history(
        crawl_result: dict,
        match_result: dict,
        report_result: dict,
        telegram_result: dict,
    ) -> dict:
        from job_intel.core.resume import load_resume_text
        from job_intel.db import session
        from job_intel.db.history import record_match_run

        matches = _read_matches(match_result["artifact_path"])
        resume_text = load_resume_text(_resume_path())
        notified_count = telegram_result["notified_count"]
        with session(_db_path()) as conn:
            match_run_id = record_match_run(
                conn,
                resume_text=resume_text,
                results=matches,
                min_score=match_result["min_score"],
                notified_count=notified_count,
            )

        return {
            **crawl_result,
            "total_matches": match_result["total_matches"],
            "qualified_matches": match_result["qualified_matches"],
            "notified_count": notified_count,
            "match_run_id": match_run_id,
            "report_path": report_result["report_path"],
            "used_llm_analysis": match_result["used_llm_analysis"],
            "agent_action": match_result.get("agent_action", {}),
            "agent_reasons": match_result.get("agent_reasons", []),
            "effective_min_score": match_result["min_score"],
        }

    @task
    def publish_pipeline_summary(summary: dict) -> dict:
        print("Job Intel Airflow summary")
        print(pprint.pformat(summary, sort_dicts=False))
        return summary

    crawl = crawl_and_import_jobs()
    initial_match = initial_match_resume(crawl)
    telegram_preview = preview_telegram_candidates(initial_match)
    quality = assess_recommendation_quality(initial_match, telegram_preview)
    agent_action = run_agent_tool_loop(quality)
    match = final_match_resume(quality, agent_action)
    report = write_match_report(match)
    telegram = send_telegram_digest(match)
    history = record_match_history(crawl, match, report, telegram)
    summary = publish_pipeline_summary(history)

    crawl >> initial_match
    initial_match >> telegram_preview >> quality >> agent_action >> match
    match >> [report, telegram]
    [report, telegram] >> history
    history >> summary


job_intel_daily()
