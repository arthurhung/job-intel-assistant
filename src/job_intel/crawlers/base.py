from __future__ import annotations

from abc import ABC, abstractmethod

from job_intel.core.models import JobPosting


class JobCrawler(ABC):
    source: str

    @abstractmethod
    def crawl(self) -> list[JobPosting]:
        """Return normalized job postings from this crawler source."""
