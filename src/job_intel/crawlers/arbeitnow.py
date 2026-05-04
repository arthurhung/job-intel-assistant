from __future__ import annotations

from job_intel.crawlers.base import JobCrawler
from job_intel.crawlers.utils import clean_html, date_from_epoch, fetch_json
from job_intel.core.models import JobPosting


ARBEITNOW_API_URL = "https://www.arbeitnow.com/api/job-board-api"


class ArbeitnowCrawler(JobCrawler):
    source = "arbeitnow"

    def __init__(self, *, limit: int = 10) -> None:
        self.limit = limit

    def crawl(self) -> list[JobPosting]:
        payload = fetch_json(ARBEITNOW_API_URL)
        jobs = payload.get("data", [])[: self.limit]
        return [self._to_posting(job) for job in jobs]

    def _to_posting(self, job: dict) -> JobPosting:
        tags = ", ".join(str(tag) for tag in job.get("tags") or [])
        description = clean_html(str(job.get("description") or ""))
        if tags:
            description = f"{description}\n\nTags: {tags}".strip()

        url = str(job.get("url") or "")
        if url:
            description = f"{description}\n\nSource: Arbeitnow ({url})".strip()

        location = str(job.get("location") or "").strip()
        if job.get("remote"):
            location = f"Remote - {location}" if location else "Remote"

        return JobPosting(
            source=self.source,
            external_id=str(job.get("slug") or url),
            title=str(job.get("title") or "").strip(),
            company=str(job.get("company_name") or "").strip(),
            location=location,
            url=url,
            description=description,
            salary="",
            posted_at=date_from_epoch(job.get("created_at")),
        )
