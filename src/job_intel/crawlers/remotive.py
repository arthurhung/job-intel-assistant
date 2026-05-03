from __future__ import annotations

import html
import json
import re
import urllib.parse
import urllib.request

from job_intel.crawlers.base import JobCrawler
from job_intel.models import JobPosting


REMOTIVE_API_URL = "https://remotive.com/api/remote-jobs"


class RemotiveCrawler(JobCrawler):
    source = "remotive"

    def __init__(self, *, search: str = "python", limit: int = 10) -> None:
        self.search = search
        self.limit = limit

    def crawl(self) -> list[JobPosting]:
        params = urllib.parse.urlencode({"search": self.search})
        request = urllib.request.Request(
            f"{REMOTIVE_API_URL}?{params}",
            headers={"User-Agent": "job-intel-assistant/0.1"},
        )
        with urllib.request.urlopen(request, timeout=20) as response:
            payload = json.loads(response.read().decode("utf-8"))

        jobs = payload.get("jobs", [])[: self.limit]
        return [self._to_posting(job) for job in jobs]

    def _to_posting(self, job: dict) -> JobPosting:
        url = str(job.get("url") or "")
        description = _clean_html(str(job.get("description") or ""))
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


def _clean_html(value: str) -> str:
    without_tags = re.sub(r"<[^>]+>", " ", value)
    compact = " ".join(html.unescape(without_tags).split())
    return compact
