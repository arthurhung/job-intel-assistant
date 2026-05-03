from __future__ import annotations

from job_intel.crawlers.base import JobCrawler
from job_intel.crawlers.remotive import RemotiveCrawler
from job_intel.crawlers.sample import SampleCrawler
from job_intel.models import JobPosting


CRAWLERS: dict[str, type[JobCrawler]] = {
    RemotiveCrawler.source: RemotiveCrawler,
    SampleCrawler.source: SampleCrawler,
    "sample": SampleCrawler,
}


def available_crawlers() -> list[str]:
    return sorted(CRAWLERS)


def crawl_jobs(source: str) -> list[JobPosting]:
    crawler_type = CRAWLERS.get(source)
    if crawler_type is None:
        options = ", ".join(available_crawlers())
        raise ValueError(f"Unknown crawler source '{source}'. Available sources: {options}")
    return crawler_type().crawl()
