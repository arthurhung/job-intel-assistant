from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class JobPosting:
    source: str
    external_id: str
    title: str
    company: str
    location: str
    url: str
    description: str
    salary: str
    posted_at: str


@dataclass(frozen=True)
class MatchResult:
    source: str
    external_id: str
    title: str
    company: str
    location: str
    url: str
    score: float
    matched_skills: list[str]
    missing_skills: list[str]
    summary: str
    llm_score: float | None = None
    llm_recommendation: str = ""
    llm_concerns: list[str] | None = None
