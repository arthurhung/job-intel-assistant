from __future__ import annotations

from job_intel.crawlers.utils import clean_html, date_from_epoch, first_date


def test_clean_html_strips_tags_and_unescapes_entities() -> None:
    assert clean_html("<p>Python&nbsp;<strong>backend</strong></p>") == "Python backend"


def test_first_date_accepts_iso_datetime_or_blank_values() -> None:
    assert first_date("2026-05-10T12:34:56") == "2026-05-10"
    assert first_date("2026-05-10 12:34:56") == "2026-05-10"
    assert first_date(None) == ""


def test_date_from_epoch_returns_utc_date() -> None:
    assert date_from_epoch(0) == "1970-01-01"
    assert date_from_epoch("not-a-timestamp") == ""
