# Airflow Pipeline

The project includes an Airflow-ready DAG at:

```text
dags/job_intel_daily.py
```

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

## Why This Shape

The DAG is intentionally thin. Crawling, matching, reporting, notification, and match history live in `job_intel.pipeline`, so the same workflow can run from CLI, Airflow, Docker, or Kubernetes CronJob.
