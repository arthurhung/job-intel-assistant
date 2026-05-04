from __future__ import annotations

import urllib.parse

from job_intel.crawlers.base import JobCrawler
from job_intel.crawlers.utils import clean_html, fetch_json, first_date
from job_intel.core.models import JobPosting


JOB104_SEARCH_API_URL = "https://www.104.com.tw/jobs/search/api/jobs"
JOB104_REFERER = "https://www.104.com.tw/jobs/search/"
DEFAULT_SEARCH_TERMS = (
    "python",
    "backend",
    "data engineer",
    "software engineer",
)


class Job104Crawler(JobCrawler):
    source = "104"

    def __init__(self, *, limit: int = 10, search_terms: tuple[str, ...] = DEFAULT_SEARCH_TERMS) -> None:
        self.limit = limit
        self.search_terms = search_terms

    def crawl(self) -> list[JobPosting]:
        jobs: list[JobPosting] = []
        seen: set[str] = set()
        per_term_limit = max(self.limit, 5)

        for term in self.search_terms:
            for item in self._search(term, limit=per_term_limit):
                job = self._to_posting(item, term)
                if not job.external_id or job.external_id in seen:
                    continue
                seen.add(job.external_id)
                jobs.append(job)
                if len(jobs) >= self.limit:
                    return jobs
        return jobs

    def _search(self, keyword: str, *, limit: int) -> list[dict]:
        params = urllib.parse.urlencode(
            {
                "ro": "0",
                "kwop": "7",
                "keyword": keyword,
                "expansionType": "area,spec,com,job,wf,wktm",
                "order": "2",
                "asc": "0",
                "page": "1",
                "mode": "s",
                "pagesize": str(limit),
                "searchJobs": "1",
                "jobsource": "job-intel-assistant",
            }
        )
        payload = fetch_json(
            f"{JOB104_SEARCH_API_URL}?{params}",
            timeout=30,
            headers={
                "Accept": "application/json, text/plain, */*",
                "Referer": JOB104_REFERER,
            },
        )
        data = payload.get("data") if isinstance(payload, dict) else []
        return data if isinstance(data, list) else []

    def _to_posting(self, item: dict, keyword: str) -> JobPosting:
        title = clean_html(str(item.get("jobName") or item.get("jobNameSnippet") or "")).strip()
        company = clean_html(str(item.get("custName") or "")).strip()
        location = clean_html(str(item.get("jobAddrNoDesc") or item.get("jobAddress") or "Taiwan")).strip()
        url = _job_url(item)
        description = _description(item, keyword, url)

        return JobPosting(
            source=self.source,
            external_id=str(item.get("jobNo") or url).strip(),
            title=title,
            company=company,
            location=location,
            url=url,
            description=description,
            salary=_salary(item),
            posted_at=first_date(item.get("appearDate") or item.get("applyDate")),
        )


def _job_url(item: dict) -> str:
    link = item.get("link") or {}
    if isinstance(link, dict):
        url = str(link.get("job") or "").strip()
        if url:
            return url

    job_no = str(item.get("jobNo") or "").strip()
    if job_no:
        return f"https://www.104.com.tw/job/{job_no}"
    return ""


def _description(item: dict, keyword: str, url: str) -> str:
    tags = item.get("tags") or {}
    tag_descriptions = []
    if isinstance(tags, dict):
        tag_descriptions = [
            str(value.get("desc") or "").strip()
            for value in tags.values()
            if isinstance(value, dict) and value.get("desc")
        ]

    parts = [
        clean_html(str(item.get("description") or item.get("descSnippet") or "")),
        f"Industry: {item.get('coIndustryDesc')}" if item.get("coIndustryDesc") else "",
        f"Keyword: {keyword}",
        f"Remote work type: {item.get('remoteWorkType')}" if item.get("remoteWorkType") else "",
        f"Tags: {', '.join(tag_descriptions)}" if tag_descriptions else "",
        f"Source: 104 ({url})" if url else "Source: 104",
    ]
    return "\n\n".join(part for part in parts if part)


def _salary(item: dict) -> str:
    low = item.get("salaryLow")
    high = item.get("salaryHigh")
    if low and high:
        return f"NTD {low}-{high}"
    if low:
        return f"NTD {low}+"
    if high:
        return f"Up to NTD {high}"
    return ""
