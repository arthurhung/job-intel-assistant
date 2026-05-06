from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from dataclasses import replace

from job_intel.config import load_env_files
from job_intel.core.models import MatchResult


OPENAI_RESPONSES_URL = "https://api.openai.com/v1/responses"
DEFAULT_MODEL = "gpt-5.5"
DEFAULT_LLM_LIMIT = 8


class LLMConfigError(RuntimeError):
    """Raised when LLM analysis is requested but configuration is missing."""


class LLMAnalysisError(RuntimeError):
    """Raised when the LLM provider cannot return a usable analysis."""


def analyze_matches_with_llm(
    results: list[MatchResult],
    *,
    resume_text: str,
    enabled: bool = False,
    limit: int = DEFAULT_LLM_LIMIT,
) -> list[MatchResult]:
    if not enabled:
        return results

    load_env_files()
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise LLMConfigError("Set OPENAI_API_KEY before enabling LLM analysis.")

    model = os.getenv("OPENAI_MODEL", DEFAULT_MODEL)
    analyzed: list[MatchResult] = []
    for index, item in enumerate(results):
        if index >= limit:
            analyzed.append(item)
            continue
        analysis = analyze_match_with_llm(
            item,
            resume_text=resume_text,
            api_key=api_key,
            model=model,
        )
        analyzed.append(
            replace(
                item,
                llm_score=analysis["fit_score"],
                llm_recommendation=analysis["recommendation"],
                llm_concerns=analysis["concerns"],
            )
        )
    return sorted(analyzed, key=lambda item: item.llm_score if item.llm_score is not None else item.score, reverse=True)


def analyze_match_with_llm(
    item: MatchResult,
    *,
    resume_text: str,
    api_key: str,
    model: str,
) -> dict:
    payload = {
        "model": model,
        "input": [
            {
                "role": "system",
                "content": [
                    {
                        "type": "input_text",
                        "text": (
                            "You evaluate whether a job fits a candidate resume. "
                            "Return concise JSON only. Be practical and conservative."
                        ),
                    }
                ],
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text": _build_prompt(item=item, resume_text=resume_text),
                    }
                ],
            },
        ],
        "text": {
            "format": {
                "type": "json_schema",
                "name": "job_fit_analysis",
                "strict": True,
                "schema": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "fit_score": {"type": "number", "minimum": 0, "maximum": 100},
                        "recommendation": {"type": "string"},
                        "concerns": {
                            "type": "array",
                            "items": {"type": "string"},
                            "maxItems": 3,
                        },
                    },
                    "required": ["fit_score", "recommendation", "concerns"],
                },
            }
        },
    }
    request = urllib.request.Request(
        OPENAI_RESPONSES_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=45) as response:
            data = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise LLMAnalysisError(
            f"OpenAI request failed with HTTP {exc.code}: {_extract_error_message(detail)}"
        ) from exc
    return _parse_response_json(data)


def _build_prompt(*, item: MatchResult, resume_text: str) -> str:
    return "\n\n".join(
        [
            "Resume:",
            resume_text[:5000],
            "Job:",
            f"Title: {item.title}",
            f"Company: {item.company}",
            f"Source: {item.source}",
            f"Location: {item.location}",
            f"Keyword score: {item.score:.1f}",
            f"Matched skills: {', '.join(item.matched_skills) or '-'}",
            f"Missing skills: {', '.join(item.missing_skills) or '-'}",
            f"Summary: {item.summary}",
            "Judge fit for this candidate. Consider skill overlap, likely seniority, location, and missing requirements.",
        ]
    )


def _parse_response_json(data: dict) -> dict:
    text = data.get("output_text")
    if not text:
        for item in data.get("output", []):
            for content in item.get("content", []):
                if content.get("type") == "output_text":
                    text = content.get("text")
                    break
            if text:
                break
    if not text:
        raise LLMAnalysisError("OpenAI response did not include output text.")

    parsed = json.loads(text)
    return {
        "fit_score": float(parsed["fit_score"]),
        "recommendation": str(parsed["recommendation"]).strip(),
        "concerns": [str(item).strip() for item in parsed.get("concerns", []) if str(item).strip()],
    }


def _extract_error_message(body: str) -> str:
    try:
        data = json.loads(body)
    except json.JSONDecodeError:
        return body[:300] or "Unknown OpenAI API error."
    error = data.get("error")
    if isinstance(error, dict):
        return str(error.get("message") or error.get("code") or "Unknown OpenAI API error.")
    return str(error or "Unknown OpenAI API error.")
