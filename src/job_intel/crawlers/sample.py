from __future__ import annotations

from job_intel.crawlers.base import JobCrawler
from job_intel.models import JobPosting


class SampleCrawler(JobCrawler):
    source = "sample-crawler"

    def crawl(self) -> list[JobPosting]:
        return [
            JobPosting(
                source=self.source,
                external_id="sample-crawler-001",
                title="Platform Data Engineer",
                company="Orbit Systems",
                location="Taipei",
                url="https://example.com/jobs/platform-data-engineer",
                description=(
                    "Own Python ETL pipelines with Airflow, Docker, PostgreSQL, "
                    "Kubernetes, data quality checks, backfills, and Telegram alerts."
                ),
                salary="Negotiable",
                posted_at="2026-05-04",
            ),
            JobPosting(
                source=self.source,
                external_id="sample-crawler-002",
                title="LLM Backend Engineer",
                company="Signal Works",
                location="Remote",
                url="https://example.com/jobs/llm-backend-engineer",
                description=(
                    "Build FastAPI services for LLM analysis workflows, SQL reporting, "
                    "web crawlers, Redis queues, Docker deployments, and observability."
                ),
                salary="Negotiable",
                posted_at="2026-05-04",
            ),
        ]
