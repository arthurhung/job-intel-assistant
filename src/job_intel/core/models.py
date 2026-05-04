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
    title: str
    company: str
    location: str
    url: str
    score: float
    matched_skills: list[str]
    missing_skills: list[str]
    summary: str
