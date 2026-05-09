# Sample Job Match Report

This is an anonymized sample output for portfolio review. Real runs write to `reports/match_report.md`.

Generated at: 2026-05-10 03:00 Asia/Taipei

Resume profile:

- Backend/data engineer
- Python, FastAPI, Airflow, Docker, PostgreSQL, Redis, SQL, AWS S3
- Interested in Taiwan-based or open remote roles

Run summary:

- Crawled sources: 104, Yourator, Cake, TaiwanJobs, Contact TAIWAN, Remote OK, Remotive, Himalayas, Arbeitnow
- Loaded jobs: 238
- Qualified jobs: 47
- Minimum score: 70.0
- Telegram candidates: 5
- Telegram dedupe: enabled
- LLM fit analysis: enabled

| Rank | Score | LLM Fit | Title | Company | Source | Location | Matched Skills | Missing Skills |
| ---: | ---: | ---: | --- | --- | --- | --- | --- | --- |
| 1 | 82.5 | 84.0 | Golang Backend Developer | Example AI Platform Co. | 104 | Taipei City | aws, docker, postgresql, python, s3, sql | sqs |
| 2 | 81.2 | 79.0 | Full-Stack Software Engineer | Example Health AI | Yourator | Taipei City | aws, docker, python | typescript |
| 3 | 81.2 | 78.0 | Principal Data Engineer | Example Data Platform | Remote OK | Remote | data quality, etl, python, sql | snowflake |
| 4 | 77.1 | 74.0 | Backend System Engineer | Example Cloud Services | 104 | New Taipei City | linux, python, redis | kubernetes |
| 5 | 75.0 | 72.0 | AI Automation Engineer | Example Electronics | 104 | New Taipei City | openai, python, sql | langgraph |

## Top Recommendation

### 1. Golang Backend Developer

- Company: Example AI Platform Co.
- Source: 104
- Location: Taipei City
- Score: 82.5
- LLM fit: 84.0
- URL: https://www.104.com.tw/job/example

Why:

The role is a strong backend fit because the resume shows production API experience, Python automation, SQL, Docker, AWS, and data pipeline exposure. The Golang requirement is a gap, but the surrounding backend and infrastructure responsibilities are aligned.

Matched skills:

- aws
- docker
- postgresql
- python
- s3
- sql

Missing skills:

- sqs

Concerns:

- Confirm whether Golang is a hard requirement or acceptable as a ramp-up skill.
- Confirm team expectations around on-call and infrastructure ownership.

Telegram digest example:

```text
Job Intel digest: 5 new match(es) >= 70.0

1. Golang Backend Developer
Company: Example AI Platform Co.
Source: 104
Location: Taipei City
Score: 82.5
LLM fit: 84.0
Why: Strong backend fit with Python, Docker, SQL, AWS, and pipeline experience.
Matched skills: aws, docker, postgresql, python, s3, sql
Missing skills: sqs
https://www.104.com.tw/job/example
```

Telegram feedback states:

- Good fit
- Not a fit
- Applied

Feedback is stored by `source + external_id + chat_id`, so jobs marked `Not a fit` or `Applied` are skipped in later Telegram digests for the same chat.
