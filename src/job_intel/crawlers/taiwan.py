from __future__ import annotations

from job_intel.crawlers.base import JobCrawler
from job_intel.crawlers.cake import CakeCrawler
from job_intel.crawlers.taiwanjobs import TaiwanJobsCrawler
from job_intel.crawlers.yourator import YouratorCrawler
from job_intel.models import JobPosting


class TaiwanCrawler(JobCrawler):
    source = "taiwan"

    def __init__(self, *, limit_per_source: int = 10) -> None:
        self.limit_per_source = limit_per_source

    def crawl(self) -> list[JobPosting]:
        crawlers: list[JobCrawler] = [
            YouratorCrawler(limit=self.limit_per_source),
            CakeCrawler(limit=self.limit_per_source),
            TaiwanJobsCrawler(limit=self.limit_per_source),
        ]
        jobs: list[JobPosting] = []
        seen: set[tuple[str, str]] = set()
        for crawler in crawlers:
            for job in crawler.crawl():
                key = (job.source, job.external_id)
                if key in seen:
                    continue
                seen.add(key)
                jobs.append(job)
        return jobs
