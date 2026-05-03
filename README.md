# Job Intel Assistant

A side-project job intelligence assistant for importing job postings, matching them against a resume, and sending high-score opportunities to Telegram.

The current version is a CLI MVP. It focuses on the core data flow before adding crawlers, LLM analysis, Airflow, and Kubernetes deployment.

## What It Does

- Imports job postings from CSV
- Stores normalized jobs in SQLite
- Reads a resume from PDF or TXT
- Extracts known skills from job descriptions and resume text
- Scores job-resume matches
- Writes a Markdown match report
- Sends top matches to Telegram

## Quick Start

```powershell
python -m pip install -e .
python -m job_intel crawl --source remoteok
python -m job_intel match --resume C:\path\to\resume.pdf --out reports\match_report.md
```

Run the full local pipeline:

```powershell
python -m job_intel run-pipeline `
  --source remotive `
  --resume C:\path\to\resume.pdf `
  --out reports\match_report.md
```

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

It also includes crawler actions that import normalized jobs through the same pipeline:

- `remotive`: remote jobs from the public Remotive API
- `remoteok`: remote jobs from the public Remote OK API
- `himalayas`: remote jobs from the public Himalayas API
- `arbeitnow`: remote and Europe-focused jobs from the public Arbeitnow API

## Telegram Notifications

Create a Telegram bot with `@BotFather`, send the bot a message, then set these environment variables:

```powershell
$env:TELEGRAM_BOT_TOKEN="your-bot-token"
$env:TELEGRAM_CHAT_ID="your-chat-id"
```

Run matching with Telegram enabled:

```powershell
python -m job_intel match `
  --resume C:\path\to\resume.pdf `
  --out reports\match_report.md `
  --notify-telegram `
  --telegram-min-score 70 `
  --telegram-limit 5
```

See [docs/telegram.md](docs/telegram.md) for setup details.

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

- Additional crawler adapters and source health tracking
- LLM-based job analysis
- Airflow DAG for scheduled ETL and notifications
- Docker Compose and Kubernetes-ready deployment

## Portfolio Positioning

This project is intended to demonstrate backend development, data pipeline design, resume-job matching, notification automation, and production-minded deployment.
