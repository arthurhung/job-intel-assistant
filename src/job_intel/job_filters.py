from __future__ import annotations

from job_intel.models import JobPosting


REMOTE_SOURCES = {"himalayas", "remoteok", "remotive"}

REMOTE_KEYWORDS = (
    "remote",
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
    normalized_source = source.strip().lower()
    if normalized_source in REMOTE_SOURCES:
        return True

    location_and_title = " ".join([location, title]).lower()
    full_text = " ".join([location, title, description]).lower()
    description_remote_phrases = (
        "fully remote",
        "remote work",
        "work remotely",
        "work from home",
        "wfh",
    )
    return (
        any(keyword in full_text for keyword in TAIWAN_KEYWORDS)
        or any(keyword in location_and_title for keyword in REMOTE_KEYWORDS)
        or any(keyword in full_text for keyword in description_remote_phrases)
    )


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
