"""Scores each posting's fit against a candidate profile. One LLM call per
posting (not a multi-turn loop) — this project's agentic shape is the
autonomous decision *pipeline* around this call (dedup, rate limiting,
threshold filtering, draft-not-submit), not multi-step tool use.
"""

from __future__ import annotations

from dataclasses import dataclass

from job_match_agent.generation.llm_client import LLMClient
from job_match_agent.profile import CandidateProfile
from job_match_agent.schema import Posting
from job_match_agent.tracing.tracer import setup_tracing

MATCH_SYSTEM_PROMPT = """You are a career advisor scoring how well a real job posting \
fits a candidate's profile. Be honest and specific — cite concrete overlaps or gaps \
between the posting's requirements and the candidate's actual skills/experience, not \
generic encouragement. Score conservatively: reserve "strong" for postings where the \
candidate would be a genuinely competitive applicant today, not just interested."""

SCORE_TOOL = {
    "name": "submit_score",
    "description": "Report the fit score, category, and reasoning for this posting.",
    "input_schema": {
        "type": "object",
        "properties": {
            "score": {"type": "integer", "minimum": 0, "maximum": 100},
            "category": {"type": "string", "enum": ["strong", "possible", "poor"]},
            "reasoning": {"type": "string", "description": "Specific overlaps/gaps, citing the posting and profile"},
        },
        "required": ["score", "category", "reasoning"],
    },
}


@dataclass
class MatchResult:
    posting: Posting
    score: int
    category: str
    reasoning: str
    input_tokens: int
    output_tokens: int


def _build_prompt(profile: CandidateProfile, posting: Posting) -> str:
    return (
        f"Candidate profile:\n{profile.to_prompt_text()}\n\n"
        f"Job posting:\nTitle: {posting.title}\nCompany: {posting.company}\n"
        f"Location: {posting.location}\nDepartment: {posting.department}\n\n"
        f"{posting.description[:3000]}"
    )


def score_posting(profile: CandidateProfile, posting: Posting, llm: LLMClient) -> MatchResult:
    tracer = setup_tracing()
    with tracer.start_as_current_span("score_posting") as span:
        span.set_attribute("company", posting.company)
        span.set_attribute("title", posting.title)

        turn = llm.create_turn(
            system=MATCH_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": _build_prompt(profile, posting)}],
            tools=[SCORE_TOOL],
        )
        call = next((tc for tc in turn.tool_calls if tc.name == "submit_score"), None)
        score = int(call.input.get("score", 0)) if call else 0
        category = call.input.get("category", "poor") if call else "poor"
        reasoning = call.input.get("reasoning", "No score returned") if call else "No score returned"

        span.set_attribute("score", score)
        span.set_attribute("category", category)

    return MatchResult(
        posting=posting,
        score=score,
        category=category,
        reasoning=reasoning,
        input_tokens=turn.input_tokens,
        output_tokens=turn.output_tokens,
    )


def score_postings(profile: CandidateProfile, postings: list[Posting], llm: LLMClient) -> list[MatchResult]:
    return [score_posting(profile, posting, llm) for posting in postings]
