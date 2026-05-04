# Airflow Pipeline

The project includes an Airflow-ready DAG at:

```text
airflow/dags/job_intel_daily.py
```

The Docker Compose setup follows Apache Airflow's local Docker quick-start shape: it is for local learning and portfolio demos, not production deployment.

The DAG calls the same reusable Python pipeline as the CLI. The intended daily workflow is:

```text
crawl Taiwan/open-remote jobs
-> filter by location policy
-> match against resume
-> write report and match history
-> send high-score Telegram digest
```

CLI equivalent:

```powershell
python -m job_intel run-pipeline --resume C:\path\to\resume.pdf --notify-telegram
```

## Environment Variables

| Variable | Default | Purpose |
| --- | --- | --- |
| `JOB_INTEL_RESUME_PATH` | required | Path to a `.pdf` or `.txt` resume |
| `JOB_INTEL_CRAWLER_SOURCE` | `all` | Crawler source |
| `JOB_INTEL_DB_PATH` | `data/job_intel.sqlite3` | SQLite database path |
| `JOB_INTEL_REPORT_PATH` | `reports/match_report.md` | Markdown report output path |
| `JOB_INTEL_ALLOWED_LOCATIONS` | optional | Comma-separated location keywords, for example `taipei,台北,新北,taoyuan,桃園,remote` |
| `JOB_INTEL_NOTIFY_TELEGRAM` | `false` | Send Telegram digest when `true`; keep `false` until bot credentials are configured |
| `JOB_INTEL_TELEGRAM_MIN_SCORE` | `70` | Minimum score for notification |
| `JOB_INTEL_TELEGRAM_LIMIT` | `5` | Maximum Telegram items |
| `TELEGRAM_BOT_TOKEN` | required for notification | Telegram bot token |
| `TELEGRAM_CHAT_ID` | required for notification | Telegram chat ID |

## Running With Docker Compose

Copy the example environment file:

```powershell
Copy-Item airflow\.env.example airflow\.env
```

Create a resume file that will be mounted into the Airflow containers:

```powershell
Copy-Item examples\resume.txt data\resume.txt
```

Initialize Airflow:

```powershell
docker compose --env-file airflow\.env -f airflow\docker-compose.yml up airflow-init
```

Start Airflow:

```powershell
docker compose --env-file airflow\.env -f airflow\docker-compose.yml up --build
```

Open the Airflow UI:

```text
http://localhost:8080
```

Default local credentials:

```text
airflow / airflow
```

Then find the `job_intel_daily` DAG, unpause it, and trigger it manually.

To make it a real daily Telegram alert, set these values in `airflow/.env`:

```text
JOB_INTEL_CRAWLER_SOURCE=all
JOB_INTEL_ALLOWED_LOCATIONS=taipei,台北,臺北,new taipei,新北,taoyuan,桃園,remote
JOB_INTEL_NOTIFY_TELEGRAM=true
JOB_INTEL_TELEGRAM_MIN_SCORE=70
JOB_INTEL_TELEGRAM_LIMIT=5
TELEGRAM_BOT_TOKEN=...
TELEGRAM_CHAT_ID=...
```

To stop the containers:

```powershell
docker compose --env-file airflow\.env -f airflow\docker-compose.yml down
```

To fully reset Airflow metadata:

```powershell
docker compose --env-file airflow\.env -f airflow\docker-compose.yml down --volumes
```

## Why This Shape

The DAG is intentionally thin. Crawling, matching, reporting, notification, and match history live in `job_intel.pipeline`, so the same Telegram alert workflow can run from CLI, Airflow, Docker, or Kubernetes CronJob.
