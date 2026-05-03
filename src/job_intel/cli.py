from __future__ import annotations

import argparse
from pathlib import Path

from job_intel.crawlers import available_crawlers, crawl_jobs
from job_intel.db import connect
from job_intel.importer import read_jobs_csv, upsert_jobs
from job_intel.matcher import match_jobs
from job_intel.report import write_markdown_report
from job_intel.resume import load_resume_text
from job_intel.telegram import TelegramConfigError, send_match_digest


DEFAULT_DB = Path("data/job_intel.sqlite3")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Job Intelligence Assistant")
    parser.add_argument("--db", default=str(DEFAULT_DB), help="SQLite database path")
    subparsers = parser.add_subparsers(dest="command", required=True)

    import_parser = subparsers.add_parser("import-jobs", help="Import jobs from a CSV file")
    import_parser.add_argument("--csv", required=True, help="Path to jobs CSV")

    crawl_parser = subparsers.add_parser("crawl", help="Crawl jobs from a configured source")
    crawl_parser.add_argument("--source", default="sample", choices=available_crawlers(), help="Crawler source")

    match_parser = subparsers.add_parser("match", help="Match imported jobs against a resume")
    match_parser.add_argument("--resume", required=True, help="Path to resume .pdf or .txt")
    match_parser.add_argument("--out", default="reports/match_report.md", help="Markdown report path")
    match_parser.add_argument("--notify-telegram", action="store_true", help="Send top matches to Telegram")
    match_parser.add_argument("--telegram-token", help="Telegram bot token. Defaults to TELEGRAM_BOT_TOKEN")
    match_parser.add_argument("--telegram-chat-id", help="Telegram chat ID. Defaults to TELEGRAM_CHAT_ID")
    match_parser.add_argument("--telegram-min-score", type=float, default=70.0, help="Minimum score to notify")
    match_parser.add_argument("--telegram-limit", type=int, default=5, help="Maximum matches to send")

    args = parser.parse_args(argv)
    db_path = Path(args.db)

    if args.command == "import-jobs":
        with connect(db_path) as conn:
            jobs = read_jobs_csv(Path(args.csv))
            count = upsert_jobs(conn, jobs)
        print(f"Imported {count} jobs into {db_path}")
        return 0

    if args.command == "crawl":
        jobs = crawl_jobs(args.source)
        with connect(db_path) as conn:
            count = upsert_jobs(conn, jobs)
        print(f"Crawled and imported {count} jobs from {args.source} into {db_path}")
        return 0

    if args.command == "match":
        resume_text = load_resume_text(Path(args.resume))
        with connect(db_path) as conn:
            results = match_jobs(conn, resume_text)
        write_markdown_report(results, Path(args.out))
        print(f"Wrote {len(results)} matches to {args.out}")
        if args.notify_telegram:
            try:
                notified = send_match_digest(
                    results,
                    token=args.telegram_token,
                    chat_id=args.telegram_chat_id,
                    min_score=args.telegram_min_score,
                    limit=args.telegram_limit,
                )
            except TelegramConfigError as exc:
                parser.error(str(exc))
            print(f"Sent Telegram digest with {notified} matches")
        return 0

    return 1
