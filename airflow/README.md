# Airflow Pipeline

The project includes an Airflow-ready DAG at:

```text
airflow/dags/job_intel_daily.py
```

The Docker Compose setup follows Apache Airflow's local Docker quick-start shape: it is for local learning and portfolio demos, not production deployment.

The DAG splits the workflow into separate Airflow tasks so each step can be retried and inspected from the UI:

```text
crawl_and_import_jobs
-> match_resume
-> write_match_report
-> send_telegram_digest
-> record_match_history
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
| `JOB_INTEL_CRAWLER_LIMIT_PER_SOURCE` | `25` | Maximum jobs to request from each crawler source |
| `JOB_INTEL_DB_PATH` | `data/job_intel.sqlite3` | SQLite database path |
| `JOB_INTEL_REPORT_PATH` | `reports/match_report.md` | Markdown report output path |
| `JOB_INTEL_AIRFLOW_ARTIFACT_DIR` | `data/airflow` | JSON artifact directory used to pass matches between Airflow tasks |
| `JOB_INTEL_ALLOWED_LOCATIONS` | optional | Comma-separated location keywords, for example `taipei,台北,臺北,new taipei,新北,taoyuan,桃園,remote` |
| `JOB_INTEL_USE_LLM_ANALYSIS` | `false` | Use OpenAI to add LLM fit scores and recommendation notes |
| `JOB_INTEL_NOTIFY_TELEGRAM` | `false` | Send Telegram digest when `true`; keep `false` until bot credentials are configured |
| `JOB_INTEL_TELEGRAM_MIN_SCORE` | `70` | Minimum score for notification |
| `JOB_INTEL_TELEGRAM_LIMIT` | `5` | Maximum Telegram items |
| `TELEGRAM_BOT_TOKEN` | required for notification | Telegram bot token |
| `TELEGRAM_CHAT_ID` | required for notification | Telegram chat ID |
| `OPENAI_API_KEY` | required for LLM analysis | OpenAI API key |
| `OPENAI_MODEL` | `gpt-5.5` | OpenAI model for fit analysis |

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
OPENAI_API_KEY=...
JOB_INTEL_USE_LLM_ANALYSIS=true
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

The DAG keeps orchestration in Airflow and business logic in the `job_intel` package. This makes the task graph easy to observe while still allowing the same workflow pieces to run from CLI, Docker, or a future Kubernetes CronJob.
