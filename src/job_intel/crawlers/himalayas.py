from __future__ import annotations

import urllib.parse

from job_intel.crawlers.base import JobCrawler
from job_intel.crawlers.utils import clean_html, fetch_json, first_date
from job_intel.core.models import JobPosting


HIMALAYAS_SEARCH_URL = "https://himalayas.app/jobs/api/search"


class HimalayasCrawler(JobCrawler):
    source = "himalayas"

    def __init__(self, *, search: str = "python", limit: int = 10) -> None:
        self.search = search
        self.limit = min(limit, 20)

    def crawl(self) -> list[JobPosting]:
        params = urllib.parse.urlencode({"q": self.search, "sort": "recent", "page": 1})
        payload = fetch_json(f"{HIMALAYAS_SEARCH_URL}?{params}")
        jobs = payload.get("jobs", [])[: self.limit]
        return [self._to_posting(job) for job in jobs]

    def _to_posting(self, job: dict) -> JobPosting:
        categories = ", ".join(str(category) for category in job.get("categories") or [])
        description = clean_html(str(job.get("description") or job.get("excerpt") or ""))
        if categories:
            description = f"{description}\n\nCategories: {categories}".strip()

        url = str(job.get("applicationLink") or "")
        if url:
            description = f"{description}\n\nSource: Himalayas ({url})".strip()

        location = ", ".join(str(item) for item in job.get("locationRestrictions") or [])
        salary = _format_salary(job)

        return JobPosting(
            source=self.source,
            external_id=str(job.get("guid") or url),
            title=str(job.get("title") or "").strip(),
            company=str(job.get("companyName") or "").strip(),
            location=location or "Worldwide remote",
            url=url,
            description=description,
            salary=salary,
            posted_at=first_date(job.get("pubDate")),
        )


def _format_salary(job: dict) -> str:
    min_salary = job.get("minSalary")
    max_salary = job.get("maxSalary")
    currency = str(job.get("currency") or "").strip()
    if min_salary and max_salary:
        if min_salary == max_salary:
            return f"{currency} {min_salary}".strip()
        return f"{currency} {min_salary}-{max_salary}".strip()
    if min_salary:
        return f"{currency} {min_salary}+".strip()
    if max_salary:
        return f"Up to {currency} {max_salary}".strip()
    return ""
