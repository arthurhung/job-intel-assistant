from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class AppSettings:
    root_dir: Path = ROOT_DIR
    db_path: Path = ROOT_DIR / "data" / "job_intel.sqlite3"
    web_dir: Path = ROOT_DIR / "web" / "dist"
    default_report_path: Path = ROOT_DIR / "reports" / "match_report.md"


def get_settings() -> AppSettings:
    return AppSettings(
        db_path=Path(os.getenv("JOB_INTEL_DB_PATH", ROOT_DIR / "data" / "job_intel.sqlite3")),
        web_dir=Path(os.getenv("JOB_INTEL_WEB_DIR", ROOT_DIR / "web" / "dist")),
        default_report_path=Path(
            os.getenv("JOB_INTEL_REPORT_PATH", ROOT_DIR / "reports" / "match_report.md")
        ),
    )
