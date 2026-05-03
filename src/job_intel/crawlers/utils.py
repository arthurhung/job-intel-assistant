from __future__ import annotations

import html
import json
import re
import urllib.request
from datetime import UTC, datetime
from typing import Any


DEFAULT_USER_AGENT = "job-intel-assistant/0.1"


def fetch_json(url: str, *, timeout: int = 20) -> Any:
    request = urllib.request.Request(url, headers={"User-Agent": DEFAULT_USER_AGENT})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8", errors="replace"))


def clean_html(value: str) -> str:
    without_tags = re.sub(r"<[^>]+>", " ", value)
    compact = " ".join(html.unescape(without_tags).split())
    return compact


def first_date(value: object) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    if not text:
        return ""
    return text.split("T")[0].split(" ")[0]


def date_from_epoch(value: object) -> str:
    try:
        timestamp = int(value)
    except (TypeError, ValueError):
        return ""
    return datetime.fromtimestamp(timestamp, tz=UTC).date().isoformat()
