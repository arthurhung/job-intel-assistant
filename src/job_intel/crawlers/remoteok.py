from __future__ import annotations

from job_intel.crawlers.base import JobCrawler
from job_intel.crawlers.utils import clean_html, fetch_json, first_date
from job_intel.models import JobPosting


REMOTEOK_API_URL = "https://remoteok.com/api"


class RemoteOkCrawler(JobCrawler):
    source = "remoteok"

    def __init__(self, *, limit: int = 10) -> None:
        self.limit = limit

    def crawl(self) -> list[JobPosting]:
        payload = fetch_json(REMOTEOK_API_URL, timeout=30)
        jobs = [item for item in payload if isinstance(item, dict) and item.get("id")]
        return [self._to_posting(job) for job in jobs[: self.limit]]

    def _to_posting(self, job: dict) -> JobPosting:
        tags = ", ".join(str(tag) for tag in job.get("tags") or [])
        description = clean_html(str(job.get("description") or ""))
        if tags:
            description = f"{description}\n\nTags: {tags}".strip()

        url = str(job.get("url") or "")
        if url:
            description = f"{description}\n\nSource: Remote OK ({url})".strip()

        return JobPosting(
            source=self.source,
            external_id=str(job.get("id") or url),
            title=str(job.get("position") or "").strip(),
            company=clean_html(str(job.get("company") or "")).strip(),
            location=str(job.get("location") or "Remote").strip(),
            url=url,
            description=description,
            salary=_format_salary(job),
            posted_at=first_date(job.get("date")),
        )


def _format_salary(job: dict) -> str:
    min_salary = job.get("salary_min")
    max_salary = job.get("salary_max")
    if min_salary and max_salary:
        return f"USD {min_salary}-{max_salary}"
    if min_salary:
        return f"USD {min_salary}+"
    if max_salary:
        return f"Up to USD {max_salary}"
    return ""
