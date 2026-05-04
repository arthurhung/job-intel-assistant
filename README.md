# Job Intel Assistant

A scheduled job intelligence assistant that crawls Taiwan and open-remote job sources, ranks roles against a resume, and sends high-signal opportunities to Telegram.

The long-term goal is a hands-off job alert pipeline: Airflow runs the workflow daily, filters out low-signal roles, and pushes only relevant opportunities to Telegram.

## What It Does

- Crawls Taiwan and open-remote job sources
- Stores normalized jobs in SQLite
- Reads a resume from PDF or TXT
- Extracts known skills from job descriptions and resume text
- Scores job-resume matches
- Writes a Markdown match report
- Sends top matches to Telegram
- Skips Telegram jobs that were already sent to the same chat
- Runs as a scheduled Airflow pipeline with Docker Compose

## Quick Start

```powershell
python -m pip install -e .
python -m job_intel crawl --source taiwan
python -m job_intel crawl --source remoteok
python -m job_intel match --resume C:\path\to\resume.pdf --out reports\match_report.md
```

Run the full local pipeline:

```powershell
python -m job_intel run-pipeline `
  --source taiwan `
  --resume C:\path\to\resume.pdf `
  --out reports\match_report.md `
  --notify-telegram `
  --telegram-min-score 70 `
  --telegram-limit 5
```

For daily automation, run the Airflow Docker setup and enable Telegram notification in `airflow/.env`.

## Web Dashboard

Run the FastAPI API server:

```powershell
python -m uvicorn job_intel.api:app --reload
```

Run the React dashboard in development mode:

```powershell
npm.cmd --prefix web install
npm.cmd --prefix web run dev
```

Then visit:

```text
http://127.0.0.1:5173
```

The Vite dev server proxies `/api` requests to FastAPI at `http://127.0.0.1:8000`.

To serve the built dashboard from FastAPI:

```powershell
npm.cmd --prefix web run build
python -m uvicorn job_intel.api:app --reload
```

Then visit:

```text
http://127.0.0.1:8000
```

The dashboard lets you upload or paste resume text, run matching against imported jobs, filter by score/skill/company, inspect matched and missing skills, review recent match runs, and optionally send a Telegram digest.

Matching is intentionally scoped to Taiwan-based or open remote jobs. Country-restricted remote roles outside Taiwan are skipped before import and ignored during matching.

It also includes crawler actions that import normalized jobs through the same pipeline:

- `remotive`: remote jobs from the public Remotive API
- `remoteok`: remote jobs from the public Remote OK API
- `himalayas`: remote jobs from the public Himalayas API
- `arbeitnow`: remote and Europe-focused jobs from the public Arbeitnow API
- `taiwan`: Taiwan source aggregate across Yourator, Cake, and TaiwanJobs
- `yourator`: Taiwan startup and digital jobs from Yourator
- `cake`: Taiwan jobs from Cake
- `taiwanjobs`: Taiwan public job listings from TaiwanJobs OpenData

## Telegram Notifications

Create a Telegram bot with `@BotFather`, send the bot a message, then copy `.env.example` to `.env` and set:

```powershell
TELEGRAM_BOT_TOKEN=your-bot-token
TELEGRAM_CHAT_ID=your-chat-id
```

Verify the credentials:

```powershell
python -m job_intel test-telegram
```

Run the full crawler + matcher pipeline with Telegram enabled:

```powershell
python -m job_intel run-pipeline `
  --source taiwan `
  --resume C:\path\to\resume.pdf `
  --out reports\match_report.md `
  --notify-telegram `
  --telegram-min-score 70 `
  --telegram-limit 5
```

See [docs/telegram.md](docs/telegram.md) for setup details.

The app reads `.env` and `.env.local` automatically. Telegram commands can also reuse `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` from `airflow/.env`. Existing environment variables take priority. Airflow reads `airflow/.env` through Docker Compose.

Telegram notifications are deduplicated by `source + external_id + chat_id`, so the same job is not pushed again after a successful send.

## CSV Format

```csv
source,external_id,title,company,location,url,description,salary,posted_at
```

## Roadmap

See [docs/roadmap.md](docs/roadmap.md).

Airflow scheduling notes are in [airflow/README.md](airflow/README.md).

Project structure notes are in [docs/architecture.md](docs/architecture.md).

Docker Compose files for running Airflow locally:

- [airflow/Dockerfile](airflow/Dockerfile)
- [airflow/docker-compose.yml](airflow/docker-compose.yml)
- [airflow/.env.example](airflow/.env.example)

Planned milestones:

- Notification deduplication so the same job is not pushed every day
- Source health tracking for crawler failures
- LLM-based job analysis
- Kubernetes-ready deployment

## Portfolio Positioning

This project is intended to demonstrate backend development, data pipeline design, scheduled automation, resume-job matching, Telegram notification workflows, and production-minded deployment.
