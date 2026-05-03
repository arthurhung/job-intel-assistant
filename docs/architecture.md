# Architecture

The project is organized around a thin-interface / shared-service shape:

```text
web dashboard
    -> FastAPI routes
        -> service layer
            -> crawlers, matcher, importer, notifier, database

CLI
    -> service layer / pipeline

Airflow DAG
    -> pipeline
```

## Key Modules

| Module | Responsibility |
| --- | --- |
| `job_intel.config` | Central paths and environment-backed settings |
| `job_intel.schemas` | FastAPI request/response models |
| `job_intel.services` | Application use cases for API and dashboard flows |
| `job_intel.pipeline` | End-to-end crawl, match, report, notify workflow |
| `job_intel.db` | SQLite connection and schema initialization |
| `job_intel.crawlers` | Pluggable crawler adapters |
| `dags/job_intel_daily.py` | Airflow scheduling wrapper around the pipeline |

## Design Notes

- Routes stay thin and translate HTTP concerns into service calls.
- Pipeline logic is not tied to Airflow, so it can run from CLI, Docker, or a future Kubernetes CronJob.
- Runtime data such as SQLite files, logs, local resumes, and environment files are ignored by Git.
- Match history stores a redacted resume preview instead of the full resume text.
