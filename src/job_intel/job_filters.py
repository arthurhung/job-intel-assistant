from __future__ import annotations

from job_intel.models import JobPosting


OPEN_REMOTE_LOCATIONS = (
    "work from home",
    "wfh",
    "worldwide",
    "anywhere",
    "global",
    "distributed",
)

TAIWAN_KEYWORDS = (
    "taiwan",
    "台灣",
    "臺灣",
    "taipei",
    "台北",
    "臺北",
    "new taipei",
    "新北",
    "taoyuan",
    "桃園",
    "hsinchu",
    "新竹",
    "miaoli",
    "苗栗",
    "taichung",
    "台中",
    "臺中",
    "changhua",
    "彰化",
    "nantou",
    "南投",
    "yunlin",
    "雲林",
    "chiayi",
    "嘉義",
    "tainan",
    "台南",
    "臺南",
    "kaohsiung",
    "高雄",
    "pingtung",
    "屏東",
    "yilan",
    "宜蘭",
    "hualien",
    "花蓮",
    "taitung",
    "台東",
    "臺東",
    "keelung",
    "基隆",
)


def is_taiwan_or_remote_job(
    *,
    source: str,
    location: str,
    description: str = "",
    title: str = "",
) -> bool:
    if _has_taiwan_signal(location=location, description=description, title=title):
        return True
    return _is_open_remote_location(location)


def _has_taiwan_signal(*, location: str, description: str, title: str) -> bool:
    full_text = " ".join([location, title, description]).lower()
    return any(keyword in full_text for keyword in TAIWAN_KEYWORDS)


def _is_open_remote_location(location: str) -> bool:
    normalized = location.strip().lower()
    if not normalized:
        return False
    if normalized == "remote":
        return True
    return any(keyword in normalized for keyword in OPEN_REMOTE_LOCATIONS)


def filter_taiwan_or_remote_jobs(jobs: list[JobPosting]) -> list[JobPosting]:
    return [
        job
        for job in jobs
        if is_taiwan_or_remote_job(
            source=job.source,
            location=job.location,
            description=job.description,
            title=job.title,
        )
    ]
