# Airflow Pipeline

The project includes an Airflow-ready DAG at:

```text
dags/job_intel_daily.py
```

The Docker Compose setup follows Apache Airflow's local Docker quick-start shape: it is for local learning and portfolio demos, not production deployment.

The DAG calls the same reusable Python pipeline as the CLI:

```powershell
python -m job_intel run-pipeline --source remotive --resume C:\path\to\resume.pdf
```

## Environment Variables

| Variable | Default | Purpose |
| --- | --- | --- |
| `JOB_INTEL_RESUME_PATH` | required | Path to a `.pdf` or `.txt` resume |
| `JOB_INTEL_CRAWLER_SOURCE` | `remotive` | Crawler source |
| `JOB_INTEL_DB_PATH` | `data/job_intel.sqlite3` | SQLite database path |
| `JOB_INTEL_REPORT_PATH` | `reports/match_report.md` | Markdown report output path |
| `JOB_INTEL_NOTIFY_TELEGRAM` | `false` | Send Telegram digest when `true` |
| `JOB_INTEL_TELEGRAM_MIN_SCORE` | `70` | Minimum score for notification |
| `JOB_INTEL_TELEGRAM_LIMIT` | `5` | Maximum Telegram items |
| `TELEGRAM_BOT_TOKEN` | required for notification | Telegram bot token |
| `TELEGRAM_CHAT_ID` | required for notification | Telegram chat ID |

## Running With Docker Compose

Copy the example environment file:

```powershell
Copy-Item .env.airflow.example .env.airflow
```

Create a resume file that will be mounted into the Airflow containers:

```powershell
Copy-Item examples\resume.txt data\resume.txt
```

Initialize Airflow:

```powershell
docker compose --env-file .env.airflow -f docker-compose.airflow.yml up airflow-init
```

Start Airflow:

```powershell
docker compose --env-file .env.airflow -f docker-compose.airflow.yml up --build
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

To stop the containers:

```powershell
docker compose --env-file .env.airflow -f docker-compose.airflow.yml down
```

To fully reset Airflow metadata:

```powershell
docker compose --env-file .env.airflow -f docker-compose.airflow.yml down --volumes
```

## Why This Shape

The DAG is intentionally thin. Crawling, matching, reporting, notification, and match history live in `job_intel.pipeline`, so the same workflow can run from CLI, Airflow, Docker, or Kubernetes CronJob.
