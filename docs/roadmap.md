# Job Intel Assistant Roadmap

This project is a portfolio-ready job intelligence assistant. The goal is to crawl Taiwan and open-remote job sources, rank jobs against a resume, and push only useful opportunities to Telegram on a schedule.

## Current Focus

- Keep the daily workflow hands-off.
- Prioritize Taiwan-based and open-remote jobs.
- Avoid duplicate Telegram notifications.
- Keep the project structure clear enough to discuss in interviews.

## MVP Status

Status: portfolio MVP complete.

The project currently runs end-to-end locally: crawlers import jobs, matching ranks them against a resume, Airflow orchestrates the scheduled pipeline, Telegram receives deduplicated digests, Telegram feedback is stored, and the dashboard shows jobs, matches, run history, and feedback state.

Remaining roadmap items are production hardening and polish, not blockers for demonstrating the core workflow.

## Phase 1 - CLI MVP

Status: done.

- Import normalized jobs into SQLite.
- Load resume text from PDF or TXT.
- Extract known skills from resumes and job descriptions.
- Score resume-to-job matches.
- Generate a Markdown match report.
- Run the workflow from `python -m job_intel`.

## Phase 2 - Crawlers

Status: MVP done; hardening in progress.

- Add crawler adapters behind a shared interface.
- Normalize jobs into `source`, `external_id`, `title`, `company`, `location`, `url`, `description`, `salary`, and `posted_at`.
- Deduplicate jobs with `source + external_id`.
- Support all configured Taiwan and open-remote sources through the default `all` aggregate crawler.
- Keep non-Taiwan, country-restricted remote roles out of the matching flow.

Next improvements:

- Add source health tracking.
- Record crawl run history.
- Improve crawler error handling and rate-limit behavior.
- Add more Taiwan job sources if they provide stable public data or acceptable HTML access.

## Phase 3 - Telegram Notifications

Status: MVP done; dashboard/history polish in progress.

- Send top matches through Telegram Bot API.
- Read `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` from `.env` or the environment.
- Support `python -m job_intel test-telegram`.
- Send only jobs above the configured score threshold.
- Skip jobs that were already sent to the same Telegram chat.
- Record Telegram feedback from inline buttons.
- Skip jobs marked as `Not a fit` or `Applied`.

Next improvements:

- Expand notification history analytics in the dashboard.
- Add more feedback-driven ranking rules.

## Phase 4 - Airflow Pipeline

Status: MVP done; production hardening in progress.

Target DAG:

```text
crawl_jobs
-> normalize_jobs
-> deduplicate_jobs
-> match_resume
-> send_telegram_notification
-> record_run_history
```

Current goals:

- Run the real pipeline inside Docker Compose.
- Load Airflow settings from `airflow/.env`.
- Use retries for crawler and notification tasks.
- Keep reports and SQLite data mounted outside the container.
- Assess recommendation quality before notification.
- Optionally run a follow-up 104 crawl with focused keywords.
- Raise the final Telegram threshold when recommendation quality is low.
- Optionally ask an LLM planner for a constrained crawl strategy before executing the tool loop.

Next improvements:

- Add source health and notification history tasks.
- Prepare the flow for PostgreSQL later.

## Phase 5 - Web Dashboard

Status: MVP done; UX polish in progress.

- FastAPI backend.
- React dashboard.
- Resume upload or pasted resume text.
- One-click all-source crawling.
- Match run history.
- Taiwan/open-remote filtering.
- Optional Telegram digest from the dashboard.

Next improvements:

- Show sent/not-sent notification status.
- Add crawler run history.
- Improve filters for source, location, score, and skills.
- Add simple auth before exposing the dashboard outside local development.

## Phase 6 - Matching Quality

Status: partially done; ranking quality improvements planned.

- Detect seniority and role type.
- Separate must-have skills from nice-to-have skills.
- Explain matched and missing skills more clearly.
- Improve LLM-based job analysis prompts and structured JSON validation.
- Keep deterministic keyword scoring as the fallback path.

## Phase 7 - Production-Minded Deployment

Status: planned.

Docker:

- FastAPI backend.
- Airflow scheduler and webserver.
- SQLite for local development.
- PostgreSQL for cloud deployment, concurrent runs, and future multi-user usage.
- Mounted data and reports directories.

Database migration path:

- Keep SQLAlchemy models as the database boundary.
- Add `JOB_INTEL_DATABASE_URL` when PostgreSQL is introduced.
- Use SQLite for local demos and PostgreSQL for deployed environments.
- Add Alembic migrations before schema changes become frequent.

Kubernetes:

- Backend Deployment and Service.
- Airflow scheduler, webserver, and worker.
- Secret management for Telegram and LLM credentials.
- ConfigMap for non-secret settings.
- CronJob or Airflow-based scheduled execution.

## Portfolio Narrative

> Built a data-driven job intelligence assistant with scheduled ETL pipelines, Taiwan/open-remote job crawling, resume-job matching, Telegram notifications, Dockerized Airflow orchestration, and production-minded deployment planning.

This project should demonstrate backend engineering, data pipeline design, automation, API design, crawler integration, notification workflows, and practical deployment thinking.
