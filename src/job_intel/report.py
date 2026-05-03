from __future__ import annotations

from pathlib import Path

from job_intel.models import MatchResult


def write_markdown_report(results: list[MatchResult], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Job Match Report",
        "",
        "| Rank | Score | Title | Company | Matched Skills | Missing Skills |",
        "| ---: | ---: | --- | --- | --- | --- |",
    ]

    for index, item in enumerate(results, start=1):
        lines.append(
            "| {rank} | {score:.1f} | [{title}]({url}) | {company} | {matched} | {missing} |".format(
                rank=index,
                score=item.score,
                title=_escape_table(item.title),
                url=item.url or "#",
                company=_escape_table(item.company),
                matched=_escape_table(", ".join(item.matched_skills) or "-"),
                missing=_escape_table(", ".join(item.missing_skills) or "-"),
            )
        )

    lines.extend(["", "## Details", ""])
    for item in results:
        lines.extend(
            [
                f"### {item.title} - {item.company}",
                "",
                f"- Score: {item.score:.1f}",
                f"- Location: {item.location or '-'}",
                f"- URL: {item.url or '-'}",
                f"- Matched skills: {', '.join(item.matched_skills) or '-'}",
                f"- Missing skills: {', '.join(item.missing_skills) or '-'}",
                f"- Summary: {item.summary}",
                "",
            ]
        )

    out_path.write_text("\n".join(lines), encoding="utf-8")


def _escape_table(value: str) -> str:
    return value.replace("|", "\\|")
