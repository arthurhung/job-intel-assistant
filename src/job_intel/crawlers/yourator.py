from __future__ import annotations

import urllib.parse

from job_intel.crawlers.base import JobCrawler
from job_intel.crawlers.utils import fetch_json
from job_intel.core.models import JobPosting


YOURATOR_API_URL = "https://www.yourator.co/api/v4/jobs"
YOURATOR_BASE_URL = "https://www.yourator.co"


class YouratorCrawler(JobCrawler):
    source = "yourator"

    def __init__(self, *, search: str = "python", limit: int = 10) -> None:
        self.search = search
        self.limit = limit

    def crawl(self) -> list[JobPosting]:
        params = urllib.parse.urlencode({"term[]": self.search, "page": 1})
        payload = fetch_json(f"{YOURATOR_API_URL}?{params}")
        jobs = payload.get("payload", {}).get("jobs", [])[: self.limit]
        return [self._to_posting(job) for job in jobs]

    def _to_posting(self, job: dict) -> JobPosting:
        company = job.get("company") or {}
        tags = [str(tag) for tag in job.get("tags") or []]
        url = _job_url(job)
        description = _description(job, tags, url)

        return JobPosting(
            source=self.source,
            external_id=str(job.get("id") or url),
            title=str(job.get("name") or "").strip(),
            company=str(company.get("brand") or company.get("enName") or "").strip(),
            location=str(job.get("location") or "Taiwan").strip(),
            url=url,
            description=description,
            salary=str(job.get("salary") or "").strip(),
            posted_at=str(job.get("lastActiveAt") or "").strip(),
        )


def _job_url(job: dict) -> str:
    external_url = str(job.get("thirdPartyUrl") or "").strip()
    if external_url:
        return external_url

    path = str(job.get("path") or "").strip()
    if path.startswith("http"):
        return path
    if path:
        return f"{YOURATOR_BASE_URL}{path}"
    return ""


def _description(job: dict, tags: list[str], url: str) -> str:
    parts = [
        str(job.get("name") or "").strip(),
        f"Location: {job.get('location')}" if job.get("location") else "",
        f"Salary: {job.get('salary')}" if job.get("salary") else "",
        f"Tags: {', '.join(tags)}" if tags else "",
        f"Last active: {job.get('lastActiveAt')}" if job.get("lastActiveAt") else "",
        f"Source: Yourator ({url})" if url else "Source: Yourator",
    ]
    return "\n\n".join(part for part in parts if part)
