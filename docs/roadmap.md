# Job Intel Assistant Roadmap

This project is a portfolio-ready job intelligence assistant. The goal is to crawl Taiwan and open-remote job sources, rank jobs against a resume, and push only useful opportunities to Telegram on a schedule.

## Current Focus

- Keep the daily workflow hands-off.
- Prioritize Taiwan-based and open-remote jobs.
- Avoid duplicate Telegram notifications.
- Keep the project structure clear enough to discuss in interviews.

## Phase 1 - CLI MVP

Status: done.

- Import normalized jobs into SQLite.
- Load resume text from PDF or TXT.
- Extract known skills from resumes and job descriptions.
- Score resume-to-job matches.
- Generate a Markdown match report.
- Run the workflow from `python -m job_intel`.

## Phase 2 - Crawlers

Status: in progress.

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

Status: in progress.

- Send top matches through Telegram Bot API.
- Read `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` from `.env` or the environment.
- Support `python -m job_intel test-telegram`.
- Send only jobs above the configured score threshold.
- Skip jobs that were already sent to the same Telegram chat.

Next improvements:

- Show why a job was notified.
- Add notification history to the dashboard.
- Support a daily digest summary when there are no new jobs, if desired.

## Phase 4 - Airflow Pipeline

Status: in progress.

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

Next improvements:

- Add clearer task boundaries in the DAG.
- Add source health and notification history tasks.
- Prepare the flow for PostgreSQL later.

## Phase 5 - Web Dashboard

Status: in progress.

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

Status: planned.

- Detect seniority and role type.
- Separate must-have skills from nice-to-have skills.
- Explain matched and missing skills more clearly.
- Add LLM-based job analysis with structured JSON output.
- Keep deterministic keyword scoring as the fallback path.

## Phase 7 - Production-Minded Deployment

Status: planned.

Docker:

- FastAPI backend.
- Airflow scheduler and webserver.
- SQLite for local development, PostgreSQL later.
- Mounted data and reports directories.

Kubernetes:

- Backend Deployment and Service.
- Airflow scheduler, webserver, and worker.
- Secret management for Telegram and LLM credentials.
- ConfigMap for non-secret settings.
- CronJob or Airflow-based scheduled execution.

## Portfolio Narrative

> Built a data-driven job intelligence assistant with scheduled ETL pipelines, Taiwan/open-remote job crawling, resume-job matching, Telegram notifications, Dockerized Airflow orchestration, and production-minded deployment planning.

This project should demonstrate backend engineering, data pipeline design, automation, API design, crawler integration, notification workflows, and practical deployment thinking.
