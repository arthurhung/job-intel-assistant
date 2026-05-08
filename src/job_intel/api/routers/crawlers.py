from __future__ import annotations

from fastapi import APIRouter, HTTPException

from job_intel.api.dependencies import SettingsDep
from job_intel.api.schemas import CrawlRequest, CrawlResponse
from job_intel.application.services import run_crawler
from job_intel.crawlers import available_crawlers

router = APIRouter()


@router.get("/crawlers")
def list_crawlers() -> dict[str, list[str]]:
    return {"sources": available_crawlers()}


@router.post("/crawl", response_model=CrawlResponse)
def run_crawl(request: CrawlRequest, settings: SettingsDep) -> dict:
    try:
        return run_crawler(
            settings.db_path,
            source=request.source,
            allowed_location_keywords=tuple(request.allowed_locations) or settings.allowed_location_keywords,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
