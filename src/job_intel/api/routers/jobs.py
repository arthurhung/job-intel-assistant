from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Query

from job_intel.api.dependencies import SettingsDep
from job_intel.api.schemas import JobResponse
from job_intel.application.services import list_jobs as list_jobs_service

router = APIRouter()


@router.get("/jobs", response_model=list[JobResponse])
def list_jobs(
    settings: SettingsDep,
    min_posted_at: Annotated[str | None, Query(description="Optional lower bound for posted_at")] = None,
) -> list[dict]:
    return list_jobs_service(
        settings.db_path,
        min_posted_at=min_posted_at,
        allowed_location_keywords=settings.allowed_location_keywords,
    )
