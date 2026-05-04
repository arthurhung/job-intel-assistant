from __future__ import annotations

from pydantic import BaseModel, Field


class JobResponse(BaseModel):
    id: int
    source: str
    external_id: str
    title: str
    company: str
    location: str = ""
    url: str = ""
    description: str
    salary: str = ""
    posted_at: str = ""
    updated_at: str = ""


class MatchRequest(BaseModel):
    resume_text: str = Field(min_length=1)
    notify_telegram: bool = False
    telegram_min_score: float = 70.0
    telegram_limit: int = Field(default=5, ge=1, le=20)


class MatchResponse(BaseModel):
    matches: list[dict]
    notified_count: int | None = None
    match_run_id: int


class ResumeParseResponse(BaseModel):
    filename: str
    text: str
    char_count: int


class MatchRunResponse(BaseModel):
    id: int
    resume_preview: str
    resume_chars: int
    min_score: float
    total_matches: int
    qualified_matches: int
    notified_count: int | None = None
    created_at: str


class CrawlRequest(BaseModel):
    source: str = "remoteok"


class CrawlResponse(BaseModel):
    source: str
    imported_count: int
    filtered_count: int = 0
    available_sources: list[str]
