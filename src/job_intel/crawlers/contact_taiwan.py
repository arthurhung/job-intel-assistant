from __future__ import annotations

import re

from job_intel.crawlers.base import JobCrawler
from job_intel.crawlers.utils import clean_html, fetch_text
from job_intel.core.models import JobPosting


CONTACT_TAIWAN_JOBS_URL = "https://contacttaiwan.tw/MainOne/JobList2.aspx"


class ContactTaiwanCrawler(JobCrawler):
    source = "contacttaiwan"

    def __init__(self, *, limit: int = 10) -> None:
        self.limit = limit

    def crawl(self) -> list[JobPosting]:
        html = fetch_text(CONTACT_TAIWAN_JOBS_URL, timeout=30)
        rows = _extract_job_tables(html)[: self.limit]
        return [self._to_posting(index, row) for index, row in enumerate(rows, start=1)]

    def _to_posting(self, index: int, row: dict[str, str]) -> JobPosting:
        company = row.get("Company Name", "")
        title = row.get("Job Categories", "")
        industry = row.get("Industries", "")
        description = "\n\n".join(
            part
            for part in [
                title,
                f"Company: {company}" if company else "",
                f"Industry: {industry}" if industry else "",
                f"Source: Contact TAIWAN ({CONTACT_TAIWAN_JOBS_URL})",
            ]
            if part
        )

        return JobPosting(
            source=self.source,
            external_id=f"{company}:{title}" if company or title else str(index),
            title=title,
            company=company,
            location="Taiwan",
            url=CONTACT_TAIWAN_JOBS_URL,
            description=description,
            salary="",
            posted_at="",
        )


def _extract_job_tables(html: str) -> list[dict[str, str]]:
    tables = re.findall(r"<table\b.*?</table>", html, flags=re.IGNORECASE | re.DOTALL)
    jobs: list[dict[str, str]] = []
    for table in tables:
        fields = {
            label: value
            for label, value in _extract_table_rows(table)
            if label in {"Company Name", "Job Categories", "Industries"}
        }
        if fields.get("Company Name") and fields.get("Job Categories"):
            jobs.append(fields)
    return jobs


def _extract_table_rows(table: str) -> list[tuple[str, str]]:
    rows: list[tuple[str, str]] = []
    for row_html in re.findall(r"<tr\b.*?</tr>", table, flags=re.IGNORECASE | re.DOTALL):
        cells = re.findall(r"<td\b[^>]*>(.*?)</td>", row_html, flags=re.IGNORECASE | re.DOTALL)
        if len(cells) < 2:
            continue
        label = clean_html(cells[0]).strip()
        value = clean_html(cells[1]).strip()
        if label and value:
            rows.append((label, value))
    return rows
