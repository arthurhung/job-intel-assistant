from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, HTTPException, Query

from job_intel.api.dependencies import SettingsDep
from job_intel.api.schemas import MatchRequest, MatchResponse, MatchRunResponse
from job_intel.application.services import create_match_run
from job_intel.application.services import list_match_runs as list_match_runs_service
from job_intel.llm import LLMAnalysisError, LLMConfigError
from job_intel.notifications.telegram import TelegramConfigError

router = APIRouter()


@router.post("/matches", response_model=MatchResponse)
def create_matches(request: MatchRequest, settings: SettingsDep) -> dict:
    try:
        return create_match_run(
            settings.db_path,
            resume_text=request.resume_text,
            use_llm_analysis=request.use_llm_analysis,
            notify_telegram=request.notify_telegram,
            telegram_min_score=request.telegram_min_score,
            telegram_limit=request.telegram_limit,
            allowed_location_keywords=tuple(request.allowed_locations) or settings.allowed_location_keywords,
        )
    except (TelegramConfigError, LLMConfigError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except LLMAnalysisError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.get("/match-runs", response_model=list[MatchRunResponse])
def list_match_runs(settings: SettingsDep, limit: Annotated[int, Query(ge=1, le=50)] = 8) -> list[dict]:
    return list_match_runs_service(settings.db_path, limit=limit)
