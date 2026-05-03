from __future__ import annotations

import re


SKILL_ALIASES = {
    "python": ["python"],
    "sql": ["sql"],
    "airflow": ["airflow"],
    "aws": ["aws"],
    "s3": ["s3"],
    "ecs": ["ecs"],
    "step functions": ["step functions", "aws step functions"],
    "eventbridge": ["eventbridge"],
    "sqs": ["sqs"],
    "cloudwatch": ["cloudwatch"],
    "docker": ["docker"],
    "postgresql": ["postgres", "postgresql"],
    "mysql": ["mysql"],
    "mssql": ["mssql"],
    "oracle": ["oracle"],
    "mongodb": ["mongodb"],
    "redis": ["redis"],
    "django": ["django"],
    "flask": ["flask"],
    "rest": ["rest"],
    "websocket": ["websocket", "websocket api", "websocket apis"],
    "etl": ["etl"],
    "elt": ["elt"],
    "data quality": ["data quality"],
    "backfill": ["backfill", "backfills"],
    "crawler": ["crawler", "crawlers", "web crawler", "web crawlers"],
    "selenium": ["selenium"],
    "llm": ["llm"],
    "linux": ["linux"],
    "gitlab ci": ["gitlab ci"],
    "jenkins": ["jenkins"],
    "kubernetes": ["kubernetes", "k8s"],
    "slurm": ["slurm"],
    "jupyterhub": ["jupyterhub"],
    "mlflow": ["mlflow"],
    "pandas": ["pandas"],
    "numpy": ["numpy"],
    "parquet": ["parquet"],
}


def extract_skills(text: str) -> list[str]:
    normalized = text.lower()
    found: list[str] = []
    for canonical, aliases in SKILL_ALIASES.items():
        if any(_contains_alias(normalized, alias) for alias in aliases):
            found.append(canonical)
    return found


def _contains_alias(normalized_text: str, alias: str) -> bool:
    pattern = r"(?<![a-z0-9])" + re.escape(alias.lower()) + r"(?![a-z0-9])"
    return bool(re.search(pattern, normalized_text))
