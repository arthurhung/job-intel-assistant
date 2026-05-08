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
    record_job_feedback,
    record_telegram_sent_jobs,
    session,
)


TELEGRAM_API_BASE = "https://api.telegram.org"
MAX_MESSAGE_LENGTH = 3900
MAX_SKILLS = 6
CALLBACK_PREFIX = "ji"
CALLBACK_ACTIONS = {
    "interested": "Good fit",
    "ignored": "Not a fit",
    "applied": "Applied",
}


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

    _send_message(token=token, chat_id=chat_id, text=f"Job Intel digest: {len(selected)} new match(es) >= {min_score:.1f}")
    for index, item in enumerate(selected, start=1):
        _send_message(
            token=token,
            chat_id=chat_id,
            text=_format_job_message(item, index=index),
            reply_markup=_feedback_keyboard(item),
        )
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


def handle_telegram_update(update: dict, *, db_path: Path, token: str | None = None) -> dict:
    load_env_files()
    token = token or os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        raise TelegramConfigError("Set TELEGRAM_BOT_TOKEN before handling Telegram callbacks.")

    callback_query = update.get("callback_query") or {}
    callback_id = str(callback_query.get("id") or "")
    data = str(callback_query.get("data") or "")
    message = callback_query.get("message") or {}
    chat = message.get("chat") or {}
    chat_id = str(chat.get("id") or "")

    parsed = _parse_feedback_callback(data)
    if not parsed or not chat_id:
        if callback_id:
            _answer_callback_query(token=token, callback_query_id=callback_id, text="Unsupported action.")
        return {"ok": False, "handled": False}

    action, source, external_id = parsed
    with session(db_path) as conn:
        record_job_feedback(
            conn,
            source=source,
            external_id=external_id,
            chat_id=chat_id,
            feedback=action,
        )

    label = CALLBACK_ACTIONS[action]
    if callback_id:
        _answer_callback_query(token=token, callback_query_id=callback_id, text=f"Recorded: {label}")
    return {
        "ok": True,
        "handled": True,
        "feedback": action,
        "source": source,
        "external_id": external_id,
        "chat_id": chat_id,
    }


def _format_job_message(item: MatchResult, *, index: int) -> str:
    lines = [
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
        f"Summary: {_truncate(item.summary, 420)}",
        item.url or "",
    ]
    return _truncate_message("\n".join(lines).strip())


def _feedback_keyboard(item: MatchResult) -> dict | None:
    callback_rows = []
    for action, label in CALLBACK_ACTIONS.items():
        callback_data = _feedback_callback_data(action=action, source=item.source, external_id=item.external_id)
        if len(callback_data.encode("utf-8")) > 64:
            return None
        callback_rows.append({"text": label, "callback_data": callback_data})
    return {"inline_keyboard": [callback_rows]}


def _feedback_callback_data(*, action: str, source: str, external_id: str) -> str:
    return "|".join([CALLBACK_PREFIX, action, source, external_id])


def _parse_feedback_callback(data: str) -> tuple[str, str, str] | None:
    parts = data.split("|", 3)
    if len(parts) != 4:
        return None
    prefix, action, source, external_id = parts
    if prefix != CALLBACK_PREFIX or action not in CALLBACK_ACTIONS or not source or not external_id:
        return None
    return action, source, external_id


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


def _send_message(*, token: str, chat_id: str, text: str, reply_markup: dict | None = None) -> None:
    url = f"{TELEGRAM_API_BASE}/bot{token}/sendMessage"
    data = {
        "chat_id": chat_id,
        "text": text,
        "disable_web_page_preview": "true",
    }
    if reply_markup:
        data["reply_markup"] = json.dumps(reply_markup, ensure_ascii=False)
    payload = urllib.parse.urlencode(data).encode("utf-8")
    request = urllib.request.Request(url, data=payload, method="POST")

    with urllib.request.urlopen(request, timeout=15) as response:
        body = response.read().decode("utf-8")
        data = json.loads(body)
        if not data.get("ok"):
            description = data.get("description", "Unknown Telegram API error")
            raise RuntimeError(description)


def _answer_callback_query(*, token: str, callback_query_id: str, text: str) -> None:
    url = f"{TELEGRAM_API_BASE}/bot{token}/answerCallbackQuery"
    payload = urllib.parse.urlencode(
        {
            "callback_query_id": callback_query_id,
            "text": text,
        }
    ).encode("utf-8")
    request = urllib.request.Request(url, data=payload, method="POST")
    with urllib.request.urlopen(request, timeout=15) as response:
        data = json.loads(response.read().decode("utf-8"))
        if not data.get("ok"):
            description = data.get("description", "Unknown Telegram API error")
            raise RuntimeError(description)
