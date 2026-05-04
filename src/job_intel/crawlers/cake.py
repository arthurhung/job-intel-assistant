from __future__ import annotations

import json
import re
import urllib.parse

from job_intel.crawlers.base import JobCrawler
from job_intel.crawlers.utils import clean_html, fetch_text, first_date
from job_intel.core.models import JobPosting


CAKE_BASE_URL = "https://www.cake.me"
CAKE_SEARCH_URL = "https://www.cake.me/jobs/in-Taiwan"


class CakeCrawler(JobCrawler):
    source = "cake"

    def __init__(self, *, search: str = "python", limit: int = 10) -> None:
        self.search = search
        self.limit = limit

    def crawl(self) -> list[JobPosting]:
        query = urllib.parse.urlencode({"query": self.search})
        html = fetch_text(f"{CAKE_SEARCH_URL}?{query}", timeout=30)
        jobs = _extract_jobs(html)[: self.limit]
        return [self._to_posting(job) for job in jobs]

    def _to_posting(self, job: dict) -> JobPosting:
        url = _job_url(job)
        tags = ", ".join(str(tag) for tag in job.get("tags") or [])
        description = clean_html(str(job.get("description") or ""))
        if tags:
            description = f"{description}\n\nTags: {tags}".strip()
        if url:
            description = f"{description}\n\nSource: Cake ({url})".strip()

        return JobPosting(
            source=self.source,
            external_id=str(job.get("path") or url),
            title=str(job.get("title") or "").strip(),
            company=str((job.get("page") or {}).get("name") or "").strip(),
            location=", ".join(str(item) for item in job.get("locations") or []) or "Taiwan",
            url=url,
            description=description,
            salary=_format_salary(job.get("salary") or {}),
            posted_at=first_date(job.get("contentUpdatedAt")),
        )


def _extract_jobs(html: str) -> list[dict]:
    match = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', html)
    if not match:
        return []
    data = json.loads(match.group(1))
    entities = (
        data.get("props", {})
        .get("pageProps", {})
        .get("initialState", {})
        .get("jobSearch", {})
        .get("entityByPathId", {})
    )
    return [item for item in entities.values() if isinstance(item, dict) and item.get("title")]


def _job_url(job: dict) -> str:
    path = str(job.get("path") or "").strip().strip("/")
    if not path:
        return ""
    return f"{CAKE_BASE_URL}/companies/{(job.get('page') or {}).get('path', '')}/jobs/{path}"


def _format_salary(salary: dict) -> str:
    currency = str(salary.get("currency") or "").strip()
    salary_type = str(salary.get("type") or "").replace("per_", "").strip()
    low = salary.get("min")
    high = salary.get("max")
    if low and high:
        return f"{currency} {low}-{high} {salary_type}".strip()
    if low:
        return f"{currency} {low}+ {salary_type}".strip()
    if high:
        return f"Up to {currency} {high} {salary_type}".strip()
    return ""
