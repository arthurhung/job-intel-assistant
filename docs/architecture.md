# Architecture

The project is organized around a thin-interface / shared-service shape:

```text
web dashboard
    -> FastAPI routes
        -> application services
            -> crawlers, core matcher, storage, notifications

CLI
    -> application services / pipeline

Airflow DAG
    -> pipeline
```

## Key Modules

| Module | Responsibility |
| --- | --- |
| `job_intel.config` | Central paths and environment-backed settings |
| `job_intel.api` | FastAPI app, routes, and request/response schemas |
| `job_intel.cli` | Command-line interface |
| `job_intel.application` | Use cases shared by API and dashboard flows |
| `job_intel.core` | Domain models, skills, resume parsing, matching, and job policy filters |
| `job_intel.crawlers` | Pluggable crawler adapters |
| `job_intel.db` | SQLite connection, job import, and match history |
| `job_intel.notifications` | Telegram notification client |
| `job_intel.pipeline` | End-to-end crawl, match, report, notify workflow |
| `airflow/dags/job_intel_daily.py` | Airflow scheduling wrapper around the pipeline |

## Design Notes

- Routes stay thin and translate HTTP concerns into service calls.
- CLI and API are entrypoint adapters; business rules stay in `application`, `core`, and `pipeline`.
- Pipeline logic is not tied to Airflow, so it can run from CLI, Docker, or a future Kubernetes CronJob.
- Runtime data such as SQLite files, logs, local resumes, and environment files are ignored by Git.
- Match history stores a redacted resume preview instead of the full resume text.
