from __future__ import annotations

from typing import Annotated

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from job_intel.config import get_settings
from job_intel.crawlers import available_crawlers
from job_intel.schemas import (
    CrawlRequest,
    CrawlResponse,
    JobResponse,
    MatchRequest,
    MatchResponse,
    MatchRunResponse,
    ResumeParseResponse,
)
from job_intel.services import (
    create_match_run,
    list_jobs as list_jobs_service,
    list_match_runs as list_match_runs_service,
    parse_resume_bytes,
    run_crawler,
)
from job_intel.telegram import TelegramConfigError


settings = get_settings()
app = FastAPI(title="Job Intel Assistant", version="0.1.0")


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/jobs", response_model=list[JobResponse])
def list_jobs(
    min_posted_at: Annotated[str | None, Query(description="Optional lower bound for posted_at")] = None,
) -> list[dict]:
    return list_jobs_service(settings.db_path, min_posted_at=min_posted_at)


@app.post("/api/resume/parse", response_model=ResumeParseResponse)
async def parse_resume(
    request: Request,
    filename: Annotated[str, Query(description="Original filename, used for file type detection")],
) -> dict:
    try:
        return parse_resume_bytes(filename=filename, body=await request.body())
    except (RuntimeError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/api/crawlers")
def list_crawlers() -> dict[str, list[str]]:
    return {"sources": available_crawlers()}


@app.post("/api/crawl", response_model=CrawlResponse)
def run_crawl(request: CrawlRequest) -> dict:
    try:
        return run_crawler(settings.db_path, source=request.source)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/matches", response_model=MatchResponse)
def create_matches(request: MatchRequest) -> dict:
    try:
        return create_match_run(
            settings.db_path,
            resume_text=request.resume_text,
            notify_telegram=request.notify_telegram,
            telegram_min_score=request.telegram_min_score,
            telegram_limit=request.telegram_limit,
        )
    except TelegramConfigError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/api/match-runs", response_model=list[MatchRunResponse])
def list_match_runs(limit: Annotated[int, Query(ge=1, le=50)] = 8) -> list[dict]:
    return list_match_runs_service(settings.db_path, limit=limit)


if settings.web_dir.exists():
    app.mount("/assets", StaticFiles(directory=settings.web_dir / "assets"), name="assets")


@app.get("/")
def dashboard() -> FileResponse:
    index = settings.web_dir / "index.html"
    if not index.exists():
        raise HTTPException(status_code=404, detail="Dashboard assets were not found.")
    return FileResponse(index)
