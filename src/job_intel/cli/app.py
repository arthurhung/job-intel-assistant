from __future__ import annotations

import argparse
from pathlib import Path

from job_intel.config import get_settings
from job_intel.crawlers import available_crawlers
from job_intel.db import session
from job_intel.db.importer import read_jobs_csv, upsert_jobs
from job_intel.core.matcher import match_jobs
from job_intel.pipeline import run_pipeline
from job_intel.pipeline.report import write_markdown_report
from job_intel.core.resume import load_resume_text
from job_intel.notifications.telegram import TelegramConfigError, send_match_digest, send_test_message


DEFAULT_DB = get_settings().db_path


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.handler(args)
    except TelegramConfigError as exc:
        parser.error(str(exc))
        return 2


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Job Intelligence Assistant")
    parser.add_argument("--db", default=str(DEFAULT_DB), help="SQLite database path")
    subparsers = parser.add_subparsers(dest="command", required=True)

    import_parser = subparsers.add_parser("import-jobs", help="Import jobs from a CSV file")
    import_parser.add_argument("--csv", required=True, help="Path to jobs CSV")
    import_parser.set_defaults(handler=handle_import_jobs)

    crawl_parser = subparsers.add_parser("crawl", help="Crawl jobs from a configured source")
    crawl_parser.add_argument("--source", default="remoteok", choices=available_crawlers(), help="Crawler source")
    crawl_parser.set_defaults(handler=handle_crawl)

    match_parser = subparsers.add_parser("match", help="Match imported jobs against a resume")
    match_parser.add_argument("--resume", required=True, help="Path to resume .pdf or .txt")
    match_parser.add_argument("--out", default="reports/match_report.md", help="Markdown report path")
    add_telegram_options(match_parser)
    match_parser.set_defaults(handler=handle_match)

    pipeline_parser = subparsers.add_parser("run-pipeline", help="Crawl, match, report, and optionally notify")
    pipeline_parser.add_argument("--source", default="taiwan", choices=available_crawlers(), help="Crawler source")
    pipeline_parser.add_argument("--resume", required=True, help="Path to resume .pdf or .txt")
    pipeline_parser.add_argument("--out", default="reports/match_report.md", help="Markdown report path")
    add_telegram_options(pipeline_parser, include_credentials=False)
    pipeline_parser.set_defaults(handler=handle_pipeline)

    telegram_parser = subparsers.add_parser("test-telegram", help="Send a test Telegram message")
    telegram_parser.add_argument("--telegram-token", help="Telegram bot token. Defaults to TELEGRAM_BOT_TOKEN")
    telegram_parser.add_argument("--telegram-chat-id", help="Telegram chat ID. Defaults to TELEGRAM_CHAT_ID")
    telegram_parser.add_argument(
        "--message",
        default="Job Intel Assistant Telegram test message.",
        help="Test message text",
    )
    telegram_parser.set_defaults(handler=handle_test_telegram)

    return parser


def add_telegram_options(parser: argparse.ArgumentParser, *, include_credentials: bool = True) -> None:
    parser.add_argument("--notify-telegram", action="store_true", help="Send top matches to Telegram")
    if include_credentials:
        parser.add_argument("--telegram-token", help="Telegram bot token. Defaults to TELEGRAM_BOT_TOKEN")
        parser.add_argument("--telegram-chat-id", help="Telegram chat ID. Defaults to TELEGRAM_CHAT_ID")
    parser.add_argument("--telegram-min-score", type=float, default=70.0, help="Minimum score to notify")
    parser.add_argument("--telegram-limit", type=int, default=5, help="Maximum matches to send")


def handle_import_jobs(args: argparse.Namespace) -> int:
    db_path = Path(args.db)
    with session(db_path) as conn:
        jobs = read_jobs_csv(Path(args.csv))
        count = upsert_jobs(conn, jobs)
    print(f"Imported {count} jobs into {db_path}")
    return 0


def handle_crawl(args: argparse.Namespace) -> int:
    from job_intel.application.services import run_crawler

    db_path = Path(args.db)
    result = run_crawler(db_path, source=args.source)
    filtered = result.get("filtered_count", 0)
    suffix = f" ({filtered} non-Taiwan/non-remote skipped)" if filtered else ""
    print(f"Crawled and imported {result['imported_count']} jobs from {args.source} into {db_path}{suffix}")
    return 0


def handle_match(args: argparse.Namespace) -> int:
    resume_text = load_resume_text(Path(args.resume))
    with session(Path(args.db)) as conn:
        results = match_jobs(conn, resume_text)

    write_markdown_report(results, Path(args.out))
    print(f"Wrote {len(results)} matches to {args.out}")

    if args.notify_telegram:
        notified = send_match_digest(
            results,
            token=args.telegram_token,
            chat_id=args.telegram_chat_id,
            min_score=args.telegram_min_score,
            limit=args.telegram_limit,
        )
        print(f"Sent Telegram digest with {notified} matches")
    return 0


def handle_pipeline(args: argparse.Namespace) -> int:
    result = run_pipeline(
        source=args.source,
        resume_path=Path(args.resume),
        db_path=Path(args.db),
        report_path=Path(args.out),
        notify_telegram=args.notify_telegram,
        telegram_min_score=args.telegram_min_score,
        telegram_limit=args.telegram_limit,
    )
    print(
        "Pipeline complete: "
        f"crawled={result.crawled_count}, "
        f"imported={result.imported_count}, "
        f"matches={result.total_matches}, "
        f"qualified={result.qualified_matches}, "
        f"notified={result.notified_count or 0}, "
        f"match_run_id={result.match_run_id}, "
        f"report={result.report_path}"
    )
    return 0


def handle_test_telegram(args: argparse.Namespace) -> int:
    send_test_message(
        token=args.telegram_token,
        chat_id=args.telegram_chat_id,
        text=args.message,
    )
    print("Sent Telegram test message")
    return 0
