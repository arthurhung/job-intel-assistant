from __future__ import annotations

import sqlite3
from dataclasses import asdict
from pathlib import Path
from typing import Annotated

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from job_intel.crawlers import available_crawlers, crawl_jobs
from job_intel.db import connect
from job_intel.importer import upsert_jobs
from job_intel.matcher import match_jobs
from job_intel.models import MatchResult
from job_intel.telegram import TelegramConfigError, send_match_digest


ROOT_DIR = Path(__file__).resolve().parents[2]
DEFAULT_DB = ROOT_DIR / "data" / "job_intel.sqlite3"
WEB_DIR = ROOT_DIR / "web"


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


class CrawlRequest(BaseModel):
    source: str = "sample"


class CrawlResponse(BaseModel):
    source: str
    imported_count: int
    available_sources: list[str]


app = FastAPI(title="Job Intel Assistant", version="0.1.0")


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/jobs", response_model=list[JobResponse])
def list_jobs(
    min_posted_at: Annotated[str | None, Query(description="Optional lower bound for posted_at")] = None,
) -> list[dict]:
    with connect(DEFAULT_DB) as conn:
        query = """
            SELECT id, source, external_id, title, company, location, url,
                   description, salary, posted_at, updated_at
            FROM jobs
        """
        params: list[str] = []
        if min_posted_at:
            query += " WHERE posted_at >= ?"
            params.append(min_posted_at)
        query += " ORDER BY posted_at DESC, updated_at DESC"
        return [dict(row) for row in conn.execute(query, params).fetchall()]


@app.get("/api/crawlers")
def list_crawlers() -> dict[str, list[str]]:
    return {"sources": available_crawlers()}


@app.post("/api/crawl", response_model=CrawlResponse)
def run_crawl(request: CrawlRequest) -> CrawlResponse:
    try:
        jobs = crawl_jobs(request.source)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    with connect(DEFAULT_DB) as conn:
        imported_count = upsert_jobs(conn, jobs)

    return CrawlResponse(
        source=request.source,
        imported_count=imported_count,
        available_sources=available_crawlers(),
    )


@app.post("/api/matches", response_model=MatchResponse)
def create_matches(request: MatchRequest) -> MatchResponse:
    with connect(DEFAULT_DB) as conn:
        results = match_jobs(conn, request.resume_text)

    notified_count: int | None = None
    if request.notify_telegram:
        try:
            notified_count = send_match_digest(
                results,
                min_score=request.telegram_min_score,
                limit=request.telegram_limit,
            )
        except TelegramConfigError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    return MatchResponse(
        matches=[_serialize_match(item) for item in results],
        notified_count=notified_count,
    )


def _serialize_match(item: MatchResult) -> dict:
    return asdict(item)


if WEB_DIR.exists():
    app.mount("/assets", StaticFiles(directory=WEB_DIR / "assets"), name="assets")


@app.get("/")
def dashboard() -> FileResponse:
    index = WEB_DIR / "index.html"
    if not index.exists():
        raise HTTPException(status_code=404, detail="Dashboard assets were not found.")
    return FileResponse(index)
