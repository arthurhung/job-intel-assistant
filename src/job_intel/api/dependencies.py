from __future__ import annotations

from functools import lru_cache
from typing import Annotated

from fastapi import Depends

from job_intel.config import AppSettings, get_settings


@lru_cache
def get_app_settings() -> AppSettings:
    return get_settings()


SettingsDep = Annotated[AppSettings, Depends(get_app_settings)]
