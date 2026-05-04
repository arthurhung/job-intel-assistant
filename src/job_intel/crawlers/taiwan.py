from __future__ import annotations

from job_intel.crawlers.base import JobCrawler
from job_intel.crawlers.cake import CakeCrawler
from job_intel.crawlers.contact_taiwan import ContactTaiwanCrawler
from job_intel.crawlers.taiwanjobs import TaiwanJobsCrawler
from job_intel.crawlers.yourator import YouratorCrawler
from job_intel.core.models import JobPosting


class TaiwanCrawler(JobCrawler):
    source = "taiwan"

    def __init__(self, *, limit_per_source: int = 10) -> None:
        self.limit_per_source = limit_per_source

    def crawl(self) -> list[JobPosting]:
        crawlers: list[JobCrawler] = [
            YouratorCrawler(limit=self.limit_per_source),
            CakeCrawler(limit=self.limit_per_source),
            TaiwanJobsCrawler(limit=self.limit_per_source),
            ContactTaiwanCrawler(limit=self.limit_per_source),
        ]
        jobs: list[JobPosting] = []
        seen: set[tuple[str, str]] = set()
        for crawler in crawlers:
            try:
                crawled_jobs = crawler.crawl()
            except Exception as exc:
                print(f"Skipping {crawler.source} crawler after error: {exc}")
                continue
            for job in crawled_jobs:
                key = (job.source, job.external_id)
                if key in seen:
                    continue
                seen.add(key)
                jobs.append(job)
        return jobs
