from __future__ import annotations

import os
from dataclasses import dataclass
from collections.abc import Iterable
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[2]
ENV_FILES = (
    ROOT_DIR / ".env",
    ROOT_DIR / ".env.local",
)


@dataclass(frozen=True)
class AppSettings:
    root_dir: Path = ROOT_DIR
    db_path: Path = ROOT_DIR / "data" / "job_intel.sqlite3"
    web_dir: Path = ROOT_DIR / "web" / "dist"
    default_report_path: Path = ROOT_DIR / "reports" / "match_report.md"
    allowed_location_keywords: tuple[str, ...] = ()
    crawler_limit_per_source: int = 25


def load_env_files() -> None:
    for env_path in ENV_FILES:
        if env_path.is_file():
            load_env_file(env_path)


def load_env_file(env_path: Path, *, allowed_keys: Iterable[str] | None = None) -> None:
    allowed = set(allowed_keys) if allowed_keys is not None else None
    for raw_line in env_path.read_text(encoding="utf-8-sig").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip("'\"")
        if allowed is not None and key not in allowed:
            continue
        if key and key not in os.environ:
            os.environ[key] = value


def get_settings() -> AppSettings:
    load_env_files()
    return AppSettings(
        db_path=Path(os.getenv("JOB_INTEL_DB_PATH", ROOT_DIR / "data" / "job_intel.sqlite3")),
        web_dir=Path(os.getenv("JOB_INTEL_WEB_DIR", ROOT_DIR / "web" / "dist")),
        default_report_path=Path(
            os.getenv("JOB_INTEL_REPORT_PATH", ROOT_DIR / "reports" / "match_report.md")
        ),
        allowed_location_keywords=parse_csv_env("JOB_INTEL_ALLOWED_LOCATIONS"),
        crawler_limit_per_source=parse_int_env("JOB_INTEL_CRAWLER_LIMIT_PER_SOURCE", 25),
    )


def parse_csv_env(name: str) -> tuple[str, ...]:
    value = os.getenv(name, "")
    return tuple(item.strip() for item in value.split(",") if item.strip())


def parse_int_env(name: str, default: int) -> int:
    value = os.getenv(name, "")
    if not value.strip():
        return default
    try:
        return int(value)
    except ValueError:
        return default
