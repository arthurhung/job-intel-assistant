from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, Request

from job_intel.api.schemas import ResumeParseResponse
from job_intel.application.services import parse_resume_bytes

router = APIRouter()


@router.post("/resume/parse", response_model=ResumeParseResponse)
async def parse_resume(
    request: Request,
    filename: Annotated[str, Query(description="Original filename, used for file type detection")],
) -> dict:
    try:
        return parse_resume_bytes(filename=filename, body=await request.body())
    except (RuntimeError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
