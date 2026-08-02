"""Orchestrates the full run: fetch -> dedup -> score -> filter -> draft.

Never submits anything. The guardrails here (dedup, a hard cap on postings
scored per run) are what make it safe to run this repeatedly against real
company APIs without becoming a nuisance or runaway cost.
"""

from __future__ import annotations

from job_match_agent.agent.drafter import draft_for_top_matches
from job_match_agent.agent.matcher import score_postings
from job_match_agent.dedup_store import DedupStore
from job_match_agent.generation.llm_client import LLMClient
from job_match_agent.greenhouse_client import (
    fetch_postings_for_companies as fetch_greenhouse,
)
from job_match_agent.lever_client import fetch_postings_for_companies as fetch_lever
from job_match_agent.profile import CandidateProfile
from job_match_agent.tracing.tracer import current_trace_id, setup_tracing

DEFAULT_GREENHOUSE_COMPANIES = ["airbnb", "stripe", "pinterest", "robinhood", "coinbase", "asana"]
DEFAULT_LEVER_COMPANIES = ["lever", "plaid", "clari"]

MAX_POSTINGS_PER_RUN = 40  # hard cap — guardrail against unbounded LLM spend per run


def run_shortlist(
    profile: CandidateProfile,
    llm: LLMClient,
    dedup_store: DedupStore,
    greenhouse_companies: list[str] | None = None,
    lever_companies: list[str] | None = None,
    limit_per_company: int = 15,
    score_threshold: int = 75,
    max_postings: int = MAX_POSTINGS_PER_RUN,
) -> dict:
    tracer = setup_tracing()
    with tracer.start_as_current_span("shortlist_run") as run_span:
        trace_id = current_trace_id()

        postings = fetch_greenhouse(greenhouse_companies or DEFAULT_GREENHOUSE_COMPANIES, limit_per_company)
        postings += fetch_lever(lever_companies or DEFAULT_LEVER_COMPANIES, limit_per_company)
        run_span.set_attribute("total_fetched", len(postings))

        unseen = dedup_store.filter_unseen(postings)
        run_span.set_attribute("total_after_dedup", len(unseen))

        capped = unseen[:max_postings]
        run_span.set_attribute("total_scored", len(capped))

        matches = score_postings(profile, capped, llm)
        matches.sort(key=lambda m: m.score, reverse=True)

        drafts = draft_for_top_matches(profile, matches, llm, score_threshold=score_threshold)
        run_span.set_attribute("drafts_generated", len(drafts))

        # Mark seen only after successful scoring, so a mid-run failure doesn't
        # silently hide postings from the next run without ever having scored them.
        dedup_store.mark_seen(capped)

        return {
            "matches": matches,
            "drafts": drafts,
            "trace_id": trace_id,
            "total_fetched": len(postings),
            "total_after_dedup": len(unseen),
            "total_scored": len(capped),
        }
