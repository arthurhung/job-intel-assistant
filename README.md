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
- Includes source, location, score, skills, recommendation reason, and job URL in Telegram messages
- Stores Telegram feedback so ignored or applied jobs are not pushed again
- Optionally uses an LLM to judge resume-job fit and explain recommendations
- Uses an Airflow tool loop to assess recommendation quality and optionally crawl more 104 jobs before notifying
- Can use an optional LLM planner to propose the follow-up crawl strategy behind guardrails
- Runs as a scheduled Airflow pipeline with Docker Compose

## Quick Start

```powershell
python -m pip install -e .
python -m job_intel crawl
python -m job_intel match --resume C:\path\to\resume.pdf --out reports\match_report.md
```

Run the full local pipeline:

```powershell
python -m job_intel run-pipeline `
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

The dashboard lets you upload or paste resume text, crawl all configured sources, run matching against imported jobs, filter by score/skill/company/source, inspect matched and missing skills, review recent match runs, and optionally send a Telegram digest.

Matching is intentionally scoped to Taiwan-based or open remote jobs. Country-restricted remote roles outside Taiwan are skipped before import and ignored during matching.
Set `JOB_INTEL_ALLOWED_LOCATIONS` to narrow the work area. For example, this keeps Taipei, New Taipei, Taoyuan, and open remote roles:

```text
JOB_INTEL_ALLOWED_LOCATIONS=taipei,台北,臺北,new taipei,新北,taoyuan,桃園,remote
```

It also includes crawler actions that import normalized jobs through the same pipeline:

- `all`: default source that crawls every configured Taiwan and open-remote source
- `remotive`: remote jobs from the public Remotive API
- `remoteok`: remote jobs from the public Remote OK API
- `himalayas`: remote jobs from the public Himalayas API
- `arbeitnow`: remote and Europe-focused jobs from the public Arbeitnow API
- `taiwan`: Taiwan source aggregate across 104, Yourator, Cake, TaiwanJobs, and Contact TAIWAN
- `104`: Taiwan jobs from 104 Job Bank
- `yourator`: Taiwan startup and digital jobs from Yourator
- `cake`: Taiwan jobs from Cake
- `taiwanjobs`: Taiwan public job listings from TaiwanJobs OpenData
- `contacttaiwan`: Taiwan international talent jobs from Contact TAIWAN

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
  --resume C:\path\to\resume.pdf `
  --out reports\match_report.md `
  --notify-telegram `
  --telegram-min-score 70 `
  --telegram-limit 5
```

See [docs/telegram.md](docs/telegram.md) for setup details.

The app reads `.env` and `.env.local` automatically. Existing environment variables take priority. Airflow reads `airflow/.env` through Docker Compose.

Telegram notifications are deduplicated by `source + external_id + chat_id`, so the same job is not pushed again after a successful send. Telegram feedback buttons can also mark a job as `Not a fit` or `Applied`, and those jobs are skipped in later notifications for the same chat.

For Telegram feedback buttons to work, expose the FastAPI server through a public HTTPS URL and register the webhook:

```powershell
python -m job_intel set-telegram-webhook --public-url https://your-static-domain.ngrok-free.app
python -m job_intel telegram-webhook-info
```

## LLM Fit Analysis

Set an OpenAI API key to enable optional LLM-based fit analysis:

```text
OPENAI_API_KEY=your-api-key
OPENAI_MODEL=gpt-5.5
```

Then run:

```powershell
python -m job_intel run-pipeline `
  --resume C:\path\to\resume.pdf `
  --use-llm-analysis `
  --notify-telegram
```

The deterministic skill score remains the fallback. When LLM analysis is enabled, the top matches also receive an LLM fit score, recommendation note, and concerns.

Set `JOB_INTEL_USE_LLM_PLANNER=true` to let the Airflow agent ask the LLM for a constrained follow-up crawl plan. The planner can only choose validated 104 keywords and a bounded notification threshold; if the LLM is unavailable, the rule-based plan is used.

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
