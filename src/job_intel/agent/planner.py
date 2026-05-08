from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass

from job_intel.agent.tool_loop import (
    AgentDecision,
    DEFAULT_FOLLOWUP_104_KEYWORDS,
    STRICT_MIN_SCORE_MAX,
)
from job_intel.config import load_env_files
from job_intel.llm import DEFAULT_MODEL, OPENAI_RESPONSES_URL, LLMAnalysisError


MAX_PLANNER_KEYWORDS = 6
MIN_PLANNER_SCORE = 0.0
MAX_PLANNER_SCORE = STRICT_MIN_SCORE_MAX


@dataclass(frozen=True)
class AgentPlan:
    should_followup_crawl: bool
    source: str
    keywords: tuple[str, ...]
    min_score: float
    reason: str
    planner: str = "rule"

    def to_dict(self) -> dict:
        data = asdict(self)
        data["keywords"] = list(self.keywords)
        return data


def plan_with_llm(
    *,
    resume_text: str,
    agent_decision: AgentDecision,
    allowed_keywords: tuple[str, ...] = DEFAULT_FOLLOWUP_104_KEYWORDS,
    enabled: bool = False,
) -> AgentPlan:
    fallback = plan_from_rule_decision(agent_decision)
    if not enabled:
        return fallback

    load_env_files()
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return fallback

    payload = _build_planner_payload(
        resume_text=resume_text,
        agent_decision=agent_decision,
        allowed_keywords=allowed_keywords,
    )
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
    except (urllib.error.HTTPError, TimeoutError, OSError, json.JSONDecodeError):
        return fallback

    try:
        parsed = _parse_response_json(data)
        return _validate_plan(parsed, fallback=fallback, allowed_keywords=allowed_keywords)
    except (KeyError, TypeError, ValueError, json.JSONDecodeError, LLMAnalysisError):
        return fallback


def plan_from_rule_decision(agent_decision: AgentDecision) -> AgentPlan:
    reason = "; ".join(agent_decision.reasons)
    return AgentPlan(
        should_followup_crawl=agent_decision.should_followup_crawl_104,
        source="104",
        keywords=agent_decision.followup_keywords,
        min_score=agent_decision.effective_min_score,
        reason=reason,
        planner="rule",
    )


def _build_planner_payload(
    *,
    resume_text: str,
    agent_decision: AgentDecision,
    allowed_keywords: tuple[str, ...],
) -> dict:
    return {
        "model": os.getenv("OPENAI_MODEL", DEFAULT_MODEL),
        "input": [
            {
                "role": "system",
                "content": [
                    {
                        "type": "input_text",
                        "text": (
                            "You are a conservative job-search planning agent. "
                            "Return JSON only. You may only choose source '104'. "
                            "Choose keywords from the allowed keyword list. "
                            "Prefer fewer, focused keywords for Taiwan backend/data roles."
                        ),
                    }
                ],
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text": "\n\n".join(
                            [
                                "Resume excerpt:",
                                resume_text[:3500],
                                "Current quality assessment:",
                                json.dumps(agent_decision.to_dict(), ensure_ascii=False),
                                "Allowed keywords:",
                                json.dumps(list(allowed_keywords), ensure_ascii=False),
                                "Plan whether to do a follow-up crawl and what final notification threshold to use.",
                            ]
                        ),
                    }
                ],
            },
        ],
        "text": {
            "format": {
                "type": "json_schema",
                "name": "job_agent_plan",
                "strict": True,
                "schema": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "should_followup_crawl": {"type": "boolean"},
                        "source": {"type": "string", "enum": ["104"]},
                        "keywords": {
                            "type": "array",
                            "items": {"type": "string"},
                            "maxItems": MAX_PLANNER_KEYWORDS,
                        },
                        "min_score": {"type": "number", "minimum": MIN_PLANNER_SCORE, "maximum": MAX_PLANNER_SCORE},
                        "reason": {"type": "string"},
                    },
                    "required": ["should_followup_crawl", "source", "keywords", "min_score", "reason"],
                },
            }
        },
    }


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
    return json.loads(text)


def _validate_plan(parsed: dict, *, fallback: AgentPlan, allowed_keywords: tuple[str, ...]) -> AgentPlan:
    allowed = set(allowed_keywords)
    keywords = tuple(
        keyword.strip()
        for keyword in parsed["keywords"]
        if isinstance(keyword, str) and keyword.strip() in allowed
    )[:MAX_PLANNER_KEYWORDS]
    should_followup = bool(parsed["should_followup_crawl"])
    if should_followup and not keywords:
        keywords = fallback.keywords

    min_score = float(parsed["min_score"])
    min_score = min(MAX_PLANNER_SCORE, max(MIN_PLANNER_SCORE, min_score))
    return AgentPlan(
        should_followup_crawl=should_followup,
        source="104",
        keywords=keywords if should_followup else (),
        min_score=min_score,
        reason=str(parsed["reason"]).strip() or fallback.reason,
        planner="llm",
    )
