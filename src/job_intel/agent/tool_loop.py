from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Protocol

from job_intel.core.job_filters import filter_taiwan_or_remote_jobs
from job_intel.core.models import MatchResult
from job_intel.core.skills import extract_skills
from job_intel.crawlers.job104 import Job104Crawler
from job_intel.db import session
from job_intel.db.importer import upsert_jobs


DEFAULT_FOLLOWUP_104_KEYWORDS = (
    "python backend engineer",
    "data engineer python",
    "airflow data engineer",
    "backend engineer django",
    "devops python",
)
LOW_QUALITY_MIN_QUALIFIED = 5
LOW_QUALITY_MIN_AVERAGE_SCORE = 72.0
LOW_QUALITY_MIN_NOTIFIED = 3
STRICT_MIN_SCORE_BUMP = 10.0
STRICT_MIN_SCORE_MAX = 85.0


@dataclass(frozen=True)
class RecommendationQuality:
    total_matches: int
    qualified_matches: int
    notified_count: int | None
    min_score: float
    average_qualified_score: float
    top_score: float

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class AgentDecision:
    quality: RecommendationQuality
    should_followup_crawl_104: bool
    followup_keywords: tuple[str, ...]
    effective_min_score: float
    reasons: tuple[str, ...]

    def to_dict(self) -> dict:
        data = asdict(self)
        data["quality"] = self.quality.to_dict()
        data["followup_keywords"] = list(self.followup_keywords)
        data["reasons"] = list(self.reasons)
        return data


class AgentPlanLike(Protocol):
    should_followup_crawl: bool
    source: str
    keywords: tuple[str, ...]
    min_score: float
    reason: str


def assess_recommendation_quality(
    matches: list[MatchResult],
    *,
    min_score: float,
    notified_count: int | None = None,
    followup_keywords: tuple[str, ...] = DEFAULT_FOLLOWUP_104_KEYWORDS,
) -> AgentDecision:
    qualified = [item for item in matches if _ranking_score(item) >= min_score]
    average_score = (
        sum(_ranking_score(item) for item in qualified) / len(qualified)
        if qualified
        else 0.0
    )
    top_score = max((_ranking_score(item) for item in matches), default=0.0)
    quality = RecommendationQuality(
        total_matches=len(matches),
        qualified_matches=len(qualified),
        notified_count=notified_count,
        min_score=min_score,
        average_qualified_score=round(average_score, 1),
        top_score=round(top_score, 1),
    )

    reasons: list[str] = []
    if quality.qualified_matches < LOW_QUALITY_MIN_QUALIFIED:
        reasons.append(f"Only {quality.qualified_matches} match(es) reached {min_score:.1f}.")
    if quality.average_qualified_score and quality.average_qualified_score < LOW_QUALITY_MIN_AVERAGE_SCORE:
        reasons.append(f"Average qualified score is {quality.average_qualified_score:.1f}.")
    if notified_count is not None and notified_count < LOW_QUALITY_MIN_NOTIFIED:
        reasons.append(f"Only {notified_count} new Telegram notification(s) were available.")

    should_followup = bool(reasons)
    effective_min_score = min_score
    if should_followup:
        effective_min_score = min(STRICT_MIN_SCORE_MAX, min_score + STRICT_MIN_SCORE_BUMP)
        reasons.append(f"Raise notification threshold to {effective_min_score:.1f} for the final pass.")

    return AgentDecision(
        quality=quality,
        should_followup_crawl_104=should_followup,
        followup_keywords=followup_keywords if should_followup else (),
        effective_min_score=effective_min_score,
        reasons=tuple(reasons) or ("Recommendation quality is acceptable.",),
    )


def run_agent_followup_crawl(
    *,
    db_path: Path,
    allowed_location_keywords: tuple[str, ...] | None,
    decision: AgentDecision,
    limit: int,
) -> dict:
    if not decision.should_followup_crawl_104:
        return {
            "enabled": False,
            "source": "104",
            "crawled_count": 0,
            "imported_count": 0,
            "filtered_count": 0,
            "keywords": [],
            "reasons": list(decision.reasons),
        }

    crawler = Job104Crawler(limit=limit, search_terms=decision.followup_keywords)
    crawled_jobs = crawler.crawl()
    jobs = filter_taiwan_or_remote_jobs(
        crawled_jobs,
        allowed_location_keywords=allowed_location_keywords,
    )
    with session(db_path) as conn:
        imported_count = upsert_jobs(conn, jobs)

    return {
        "enabled": True,
        "source": "104",
        "crawled_count": len(crawled_jobs),
        "imported_count": imported_count,
        "filtered_count": len(crawled_jobs) - len(jobs),
        "keywords": list(decision.followup_keywords),
        "reasons": list(decision.reasons),
    }


def run_agent_plan_followup_crawl(
    *,
    db_path: Path,
    allowed_location_keywords: tuple[str, ...] | None,
    plan: AgentPlanLike,
    fallback_decision: AgentDecision,
    limit: int,
) -> dict:
    decision = AgentDecision(
        quality=fallback_decision.quality,
        should_followup_crawl_104=plan.should_followup_crawl and plan.source == "104",
        followup_keywords=plan.keywords,
        effective_min_score=plan.min_score,
        reasons=(plan.reason,),
    )
    result = run_agent_followup_crawl(
        db_path=db_path,
        allowed_location_keywords=allowed_location_keywords,
        decision=decision,
        limit=limit,
    )
    result["planner"] = getattr(plan, "planner", "unknown")
    result["min_score"] = plan.min_score
    return result


def keywords_from_resume(resume_text: str, *, fallback: tuple[str, ...] = DEFAULT_FOLLOWUP_104_KEYWORDS) -> tuple[str, ...]:
    skills = extract_skills(resume_text)
    if not skills:
        return fallback
    focused = []
    for phrase in (
        "python backend engineer",
        "data engineer",
        "backend engineer",
        "devops engineer",
    ):
        if any(skill in phrase for skill in skills):
            focused.append(phrase)
    skill_terms = [skill for skill in skills[:4] if len(skill) >= 3]
    return tuple(dict.fromkeys([*focused, *skill_terms, *fallback]))[:6]


def _ranking_score(item: MatchResult) -> float:
    return item.llm_score if item.llm_score is not None else item.score
