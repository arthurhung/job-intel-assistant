from __future__ import annotations

from job_intel.core.models import JobPosting


OPEN_REMOTE_LOCATIONS = (
    "work from home",
    "wfh",
    "worldwide",
    "anywhere",
    "global",
    "distributed",
)

REMOTE_LOCATION_KEYS = ("remote", "open remote", "worldwide", "anywhere", "global", "wfh")
DEFAULT_ALLOWED_LOCATION_KEYWORDS = ("taipei", "\u53f0\u5317", "\u81fa\u5317", "new taipei", "\u65b0\u5317", "taoyuan", "\u6843\u5712", "remote")

TAIWAN_KEYWORDS = (
    "taiwan",
    "\u53f0\u7063",
    "\u81fa\u7063",
    "taipei",
    "\u53f0\u5317",
    "\u81fa\u5317",
    "new taipei",
    "\u65b0\u5317",
    "taoyuan",
    "\u6843\u5712",
    "hsinchu",
    "\u65b0\u7af9",
    "miaoli",
    "\u82d7\u6817",
    "taichung",
    "\u53f0\u4e2d",
    "\u81fa\u4e2d",
    "changhua",
    "\u5f70\u5316",
    "nantou",
    "\u5357\u6295",
    "yunlin",
    "\u96f2\u6797",
    "chiayi",
    "\u5609\u7fa9",
    "tainan",
    "\u53f0\u5357",
    "\u81fa\u5357",
    "kaohsiung",
    "\u9ad8\u96c4",
    "pingtung",
    "\u5c4f\u6771",
    "yilan",
    "\u5b9c\u862d",
    "hualien",
    "\u82b1\u84ee",
    "taitung",
    "\u53f0\u6771",
    "\u81fa\u6771",
    "keelung",
    "\u57fa\u9686",
)


def is_taiwan_or_remote_job(
    *,
    source: str,
    location: str,
    description: str = "",
    title: str = "",
    allowed_location_keywords: tuple[str, ...] | None = None,
) -> bool:
    if allowed_location_keywords:
        return _matches_location_scope(
            location=location,
            description=description,
            title=title,
            allowed_location_keywords=allowed_location_keywords,
        )

    if _has_taiwan_signal(location=location, description=description, title=title):
        return True
    return _is_open_remote_location(location)


def _has_taiwan_signal(*, location: str, description: str, title: str) -> bool:
    full_text = " ".join([location, title, description]).lower()
    return any(keyword in full_text for keyword in TAIWAN_KEYWORDS)


def _matches_location_scope(
    *,
    location: str,
    description: str,
    title: str,
    allowed_location_keywords: tuple[str, ...],
) -> bool:
    full_text = " ".join([location, title, description]).lower()
    normalized_keywords = tuple(keyword.strip().lower() for keyword in allowed_location_keywords if keyword.strip())
    if any(keyword in full_text for keyword in normalized_keywords if keyword not in REMOTE_LOCATION_KEYS):
        return True
    if any(keyword in REMOTE_LOCATION_KEYS for keyword in normalized_keywords):
        return _is_open_remote_location(location)
    return False


def _is_open_remote_location(location: str) -> bool:
    normalized = location.strip().lower()
    if not normalized:
        return False
    if normalized == "remote":
        return True
    return any(keyword in normalized for keyword in OPEN_REMOTE_LOCATIONS)


def filter_taiwan_or_remote_jobs(
    jobs: list[JobPosting],
    *,
    allowed_location_keywords: tuple[str, ...] | None = None,
) -> list[JobPosting]:
    return [
        job
        for job in jobs
        if is_taiwan_or_remote_job(
            source=job.source,
            location=job.location,
            description=job.description,
            title=job.title,
            allowed_location_keywords=allowed_location_keywords,
        )
    ]
