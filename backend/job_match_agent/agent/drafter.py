"""Drafts a short tailored cover-letter paragraph for postings above the fit
threshold. This module ONLY drafts text — there is no function anywhere in
this codebase that submits an application to a real employer. See
docs/architecture.md for why that's a deliberate scope boundary, not a gap.
"""

from __future__ import annotations

from job_match_agent.agent.matcher import MatchResult
from job_match_agent.generation.llm_client import LLMClient
from job_match_agent.profile import CandidateProfile
from job_match_agent.tracing.tracer import setup_tracing

DRAFT_SYSTEM_PROMPT = """You draft a short (3-4 sentence) cover-letter opening paragraph \
for a candidate applying to a specific role. Cite 1-2 concrete, specific things from \
the posting and 1-2 concrete things from the candidate's background — no generic \
filler like "I am excited to apply." This is a DRAFT for the candidate to review and \
edit themselves before ever sending anything; do not write as if it's already final."""


def draft_cover_letter(profile: CandidateProfile, match: MatchResult, llm: LLMClient) -> str:
    tracer = setup_tracing()
    with tracer.start_as_current_span("draft_cover_letter") as span:
        span.set_attribute("company", match.posting.company)
        span.set_attribute("title", match.posting.title)

        prompt = (
            f"Candidate profile:\n{profile.to_prompt_text()}\n\n"
            f"Role: {match.posting.title} at {match.posting.company}\n"
            f"Why this looked like a fit: {match.reasoning}\n\n"
            f"Posting excerpt:\n{match.posting.description[:1500]}"
        )
        turn = llm.create_turn(system=DRAFT_SYSTEM_PROMPT, messages=[{"role": "user", "content": prompt}], tools=[])
        span.set_attribute("output_tokens", turn.output_tokens)

    return turn.text.strip()


def draft_for_top_matches(
    profile: CandidateProfile, matches: list[MatchResult], llm: LLMClient, score_threshold: int = 75
) -> dict[str, str]:
    """Returns {posting.dedup_key: draft_text} for matches scoring at/above the threshold."""
    drafts = {}
    for match in matches:
        if match.score >= score_threshold:
            drafts[match.posting.dedup_key] = draft_cover_letter(profile, match, llm)
    return drafts
