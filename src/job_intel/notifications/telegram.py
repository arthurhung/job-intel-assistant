from __future__ import annotations

import json
import os
from pathlib import Path
import urllib.parse
import urllib.request

from job_intel.config import load_env_files
from job_intel.core.models import MatchResult
from job_intel.db import (
    filter_unsent_telegram_matches,
    record_telegram_sent_jobs,
    session,
)


TELEGRAM_API_BASE = "https://api.telegram.org"
MAX_MESSAGE_LENGTH = 3900
MAX_SKILLS = 6


class TelegramConfigError(RuntimeError):
    """Raised when Telegram notification settings are missing."""


def send_match_digest(
    results: list[MatchResult],
    *,
    db_path: Path | None = None,
    token: str | None = None,
    chat_id: str | None = None,
    min_score: float = 70.0,
    limit: int = 5,
) -> int:
    load_env_files()
    token = token or os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = chat_id or os.getenv("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        raise TelegramConfigError(
            "Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID, or pass --telegram-token and --telegram-chat-id."
        )

    if db_path is None:
        selected = [item for item in results if item.score >= min_score][:limit]
    else:
        with session(db_path) as conn:
            selected = filter_unsent_telegram_matches(
                conn,
                results,
                chat_id=chat_id,
                min_score=min_score,
                limit=limit,
            )

    if not selected:
        return 0

    text = _format_digest(selected, min_score=min_score)

    _send_message(token=token, chat_id=chat_id, text=text)
    if db_path is not None:
        with session(db_path) as conn:
            record_telegram_sent_jobs(conn, selected, chat_id=chat_id)
    return len(selected)


def send_test_message(
    *,
    token: str | None = None,
    chat_id: str | None = None,
    text: str = "Job Intel Assistant Telegram test message.",
) -> None:
    load_env_files()
    token = token or os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = chat_id or os.getenv("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        raise TelegramConfigError(
            "Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID, or pass --telegram-token and --telegram-chat-id."
        )

    _send_message(token=token, chat_id=chat_id, text=text)


def _format_digest(results: list[MatchResult], *, min_score: float) -> str:
    lines = [
        f"Job Intel digest: {len(results)} new match(es) >= {min_score:.1f}",
        "",
    ]
    for index, item in enumerate(results, start=1):
        item_lines = [
            f"{index}. {item.title}",
            f"Company: {item.company or '-'}",
            f"Source: {item.source or '-'}",
            f"Location: {item.location or '-'}",
            f"Score: {item.score:.1f}",
            f"LLM fit: {item.llm_score:.1f}" if item.llm_score is not None else "",
            f"Why: {_recommendation_reason(item)}",
            f"LLM note: {item.llm_recommendation}" if item.llm_recommendation else "",
            f"Matched skills: {_format_skills(item.matched_skills)}",
            f"Missing skills: {_format_skills(item.missing_skills)}",
            f"Concerns: {_format_skills(item.llm_concerns or [])}" if item.llm_concerns else "",
            f"Summary: {_truncate(item.summary, 220)}",
            item.url or "",
            "",
        ]
        lines.extend(line for line in item_lines if line)
    return _truncate_message("\n".join(lines).strip())


def _recommendation_reason(item: MatchResult) -> str:
    if item.llm_recommendation:
        return item.llm_recommendation
    if item.matched_skills:
        return f"Matches {len(item.matched_skills)} skill(s) from your resume."
    if item.score >= 90:
        return "Very high score for this role."
    if item.score >= 70:
        return "Passes your notification threshold."
    return "Included by the current score filter."


def _format_skills(skills: list[str]) -> str:
    if not skills:
        return "-"
    shown = skills[:MAX_SKILLS]
    suffix = f" +{len(skills) - len(shown)} more" if len(skills) > len(shown) else ""
    return ", ".join(shown) + suffix


def _truncate(value: str, limit: int) -> str:
    compact = " ".join(value.split())
    if len(compact) <= limit:
        return compact or "-"
    return compact[: limit - 3].rstrip() + "..."


def _truncate_message(value: str) -> str:
    if len(value) <= MAX_MESSAGE_LENGTH:
        return value
    return value[: MAX_MESSAGE_LENGTH - 40].rstrip() + "\n\n[truncated]"


def _send_message(*, token: str, chat_id: str, text: str) -> None:
    url = f"{TELEGRAM_API_BASE}/bot{token}/sendMessage"
    payload = urllib.parse.urlencode(
        {
            "chat_id": chat_id,
            "text": text,
            "disable_web_page_preview": "true",
        }
    ).encode("utf-8")
    request = urllib.request.Request(url, data=payload, method="POST")

    with urllib.request.urlopen(request, timeout=15) as response:
        body = response.read().decode("utf-8")
        data = json.loads(body)
        if not data.get("ok"):
            description = data.get("description", "Unknown Telegram API error")
            raise RuntimeError(description)
