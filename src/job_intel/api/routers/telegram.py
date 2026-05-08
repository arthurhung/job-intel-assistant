from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request

from job_intel.api.dependencies import SettingsDep
from job_intel.notifications.telegram import TelegramConfigError, handle_telegram_update

router = APIRouter()


@router.post("/telegram/webhook")
async def telegram_webhook(request: Request, settings: SettingsDep) -> dict:
    try:
        return handle_telegram_update(await request.json(), db_path=settings.db_path)
    except TelegramConfigError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
