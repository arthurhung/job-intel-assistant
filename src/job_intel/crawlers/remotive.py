from __future__ import annotations

import urllib.parse

from job_intel.crawlers.base import JobCrawler
from job_intel.crawlers.utils import clean_html, fetch_json
from job_intel.core.models import JobPosting


REMOTIVE_API_URL = "https://remotive.com/api/remote-jobs"


class RemotiveCrawler(JobCrawler):
    source = "remotive"

    def __init__(self, *, search: str = "python", limit: int = 10) -> None:
        self.search = search
        self.limit = limit

    def crawl(self) -> list[JobPosting]:
        params = urllib.parse.urlencode({"search": self.search})
        payload = fetch_json(f"{REMOTIVE_API_URL}?{params}")
        jobs = payload.get("jobs", [])[: self.limit]
        return [self._to_posting(job) for job in jobs]

    def _to_posting(self, job: dict) -> JobPosting:
        url = str(job.get("url") or "")
        description = clean_html(str(job.get("description") or ""))
        if url:
            description = f"{description}\n\nSource: Remotive ({url})".strip()

        return JobPosting(
            source=self.source,
            external_id=str(job.get("id") or url),
            title=str(job.get("title") or "").strip(),
            company=str(job.get("company_name") or "").strip(),
            location=str(job.get("candidate_required_location") or "Remote").strip(),
            url=url,
            description=description,
            salary=str(job.get("salary") or "").strip(),
            posted_at=str(job.get("publication_date") or "").split("T")[0],
        )
