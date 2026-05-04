from __future__ import annotations

from job_intel.crawlers.base import JobCrawler
from job_intel.crawlers.arbeitnow import ArbeitnowCrawler
from job_intel.crawlers.cake import CakeCrawler
from job_intel.crawlers.contact_taiwan import ContactTaiwanCrawler
from job_intel.crawlers.himalayas import HimalayasCrawler
from job_intel.crawlers.remotive import RemotiveCrawler
from job_intel.crawlers.remoteok import RemoteOkCrawler
from job_intel.crawlers.taiwan import TaiwanCrawler
from job_intel.crawlers.taiwanjobs import TaiwanJobsCrawler
from job_intel.crawlers.yourator import YouratorCrawler
from job_intel.core.models import JobPosting


CRAWLERS: dict[str, type[JobCrawler]] = {
    ArbeitnowCrawler.source: ArbeitnowCrawler,
    CakeCrawler.source: CakeCrawler,
    ContactTaiwanCrawler.source: ContactTaiwanCrawler,
    HimalayasCrawler.source: HimalayasCrawler,
    RemotiveCrawler.source: RemotiveCrawler,
    RemoteOkCrawler.source: RemoteOkCrawler,
    TaiwanCrawler.source: TaiwanCrawler,
    TaiwanJobsCrawler.source: TaiwanJobsCrawler,
    YouratorCrawler.source: YouratorCrawler,
}


def available_crawlers() -> list[str]:
    return sorted(CRAWLERS)


def crawl_jobs(source: str) -> list[JobPosting]:
    crawler_type = CRAWLERS.get(source)
    if crawler_type is None:
        options = ", ".join(available_crawlers())
        raise ValueError(f"Unknown crawler source '{source}'. Available sources: {options}")
    return crawler_type().crawl()
