from __future__ import annotations

from functools import lru_cache

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from job_match_agent.dedup_store import DedupStore
from job_match_agent.generation.llm_client import get_llm_client
from job_match_agent.pipeline import run_shortlist
from job_match_agent.profile import DEMO_PROFILE
from job_match_agent.tracing.tracer import get_trace

load_dotenv()

app = FastAPI(title="Job Match & Shortlist Agent")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@lru_cache
def get_dedup_store() -> DedupStore:
    return DedupStore()


class MatchOut(BaseModel):
    company: str
    title: str
    location: str
    url: str
    score: int
    category: str
    reasoning: str
    draft: str | None = None


class ShortlistResponse(BaseModel):
    matches: list[MatchOut]
    total_fetched: int
    total_after_dedup: int
    total_scored: int
    trace_id: str
    disclaimer: str = "Nothing has been submitted anywhere. Review and apply manually."


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "seen_postings_count": get_dedup_store().count()}


@app.post("/shortlist", response_model=ShortlistResponse)
def shortlist() -> ShortlistResponse:
    try:
        llm = get_llm_client()
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    result = run_shortlist(DEMO_PROFILE, llm, get_dedup_store())

    matches_out = []
    for m in result["matches"]:
        matches_out.append(
            MatchOut(
                company=m.posting.company,
                title=m.posting.title,
                location=m.posting.location,
                url=m.posting.url,
                score=m.score,
                category=m.category,
                reasoning=m.reasoning,
                draft=result["drafts"].get(m.posting.dedup_key),
            )
        )

    return ShortlistResponse(
        matches=matches_out,
        total_fetched=result["total_fetched"],
        total_after_dedup=result["total_after_dedup"],
        total_scored=result["total_scored"],
        trace_id=result["trace_id"],
    )


@app.get("/trace/{trace_id}")
def trace(trace_id: str) -> dict:
    spans = get_trace(trace_id)
    if spans is None:
        raise HTTPException(status_code=404, detail="Trace not found (may have expired or server restarted)")
    return {"trace_id": trace_id, "spans": spans}
