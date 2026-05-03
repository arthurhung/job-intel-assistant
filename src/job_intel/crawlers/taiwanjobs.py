from __future__ import annotations

import re
import xml.etree.ElementTree as ET

from job_intel.crawlers.base import JobCrawler
from job_intel.crawlers.utils import fetch_text
from job_intel.models import JobPosting


TAIWANJOBS_API_URL = "https://free.taiwanjobs.gov.tw/webservice_taipei/Webservice.ashx?count1000"

DEFAULT_SEARCH_TERMS = (
    "python",
    "backend",
    "frontend",
    "developer",
    "engineer",
    "software",
    "data engineer",
    "data analyst",
    "data scientist",
    "cloud",
    "ai",
    "\u8edf\u9ad4",
    "\u5de5\u7a0b\u5e2b",
    "\u7a0b\u5f0f",
    "\u8cc7\u6599\u5de5\u7a0b",
    "\u8cc7\u6599\u5206\u6790",
    "\u8cc7\u6599\u79d1\u5b78",
    "\u8cc7\u6599\u5eab",
    "\u5f8c\u7aef",
    "\u524d\u7aef",
    "\u96f2\u7aef",
    "\u4eba\u5de5\u667a\u6167",
)


class TaiwanJobsCrawler(JobCrawler):
    source = "taiwanjobs"

    def __init__(self, *, limit: int = 10, search_terms: tuple[str, ...] = DEFAULT_SEARCH_TERMS) -> None:
        self.limit = limit
        self.search_terms = search_terms

    def crawl(self) -> list[JobPosting]:
        xml_text = fetch_text(
            TAIWANJOBS_API_URL,
            timeout=60,
            accept="text/xml,application/xml,*/*",
            verify_ssl=False,
        )
        rows = ET.fromstring(xml_text).findall("Data")
        jobs = [self._to_posting(row) for row in rows]
        matching_jobs = [job for job in jobs if _matches_terms(job, self.search_terms)]
        return (matching_jobs or jobs)[: self.limit]

    def _to_posting(self, row: ET.Element) -> JobPosting:
        url = _text(row, "URL_QUERY")
        job_id = _job_id_from_url(url) or f"{_text(row, 'COMPNAME')}:{_text(row, 'OCCU_DESC')}:{url}"
        description = "\n\n".join(
            part
            for part in [
                _text(row, "JOB_DETAIL"),
                f"Category: {_text(row, 'CJOB_NAME1')} / {_text(row, 'CJOB_NAME2')}",
                f"Experience: {_text(row, 'EXPERIENCE')}",
                f"Work time: {_text(row, 'WKTIME')}",
                f"Source: TaiwanJobs ({url})" if url else "Source: TaiwanJobs",
            ]
            if part and not part.endswith(": ")
        )
        return JobPosting(
            source=self.source,
            external_id=job_id,
            title=_text(row, "OCCU_DESC"),
            company=_text(row, "COMPNAME"),
            location=_text(row, "CITYNAME"),
            url=url,
            description=description,
            salary=_salary(row),
            posted_at=_date(row),
        )


def _text(row: ET.Element, tag: str) -> str:
    return (row.findtext(tag) or "").strip()


def _salary(row: ET.Element) -> str:
    salary_type = _text(row, "SALARYCD")
    low = _text(row, "NT_L")
    high = _text(row, "NT_U")
    if low and high:
        return f"{salary_type} {low}-{high}".strip()
    if low:
        return f"{salary_type} {low}+".strip()
    if high:
        return f"{salary_type} up to {high}".strip()
    return salary_type


def _date(row: ET.Element) -> str:
    value = _text(row, "TRANDATE")
    if len(value) == 8:
        return f"{value[:4]}-{value[4:6]}-{value[6:]}"
    return value


def _job_id_from_url(url: str) -> str:
    match = re.search(r"HIRE_ID=([^&]+)", url)
    return match.group(1) if match else ""


def _matches_terms(job: JobPosting, terms: tuple[str, ...]) -> bool:
    haystack = f"{job.title} {job.company}".lower()
    return any(_contains_term(haystack, term) for term in terms)


def _contains_term(haystack: str, term: str) -> bool:
    normalized = term.lower()
    if normalized.isascii():
        return bool(re.search(r"(?<![a-z0-9])" + re.escape(normalized) + r"(?![a-z0-9])", haystack))
    return normalized in haystack
