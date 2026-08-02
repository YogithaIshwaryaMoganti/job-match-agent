"""Client for the Greenhouse Job Board API (boards-api.greenhouse.io) — public,
unauthenticated, explicitly built for third-party job-board consumption. Not
scraping: this is Greenhouse's documented public API.

Confirmed live: airbnb (180 postings), stripe (548), pinterest (216),
robinhood (128), coinbase (162), asana (143) — no auth needed, `?content=true`
returns full HTML job descriptions inline (no per-job detail call required).
"""

from __future__ import annotations

import html as html_lib
import re
import time

import httpx
from bs4 import BeautifulSoup

from job_match_agent.schema import Posting

GREENHOUSE_BASE_URL = "https://boards-api.greenhouse.io/v1/boards"

_PARAGRAPH_BREAK_RE = re.compile(r"\n{2,}")
_SPACE_RUN_RE = re.compile(r"[ \t]+")


def _strip_html(raw: str) -> str:
    """Greenhouse's `content` field is HTML-entity-escaped HTML (e.g. the literal
    text "&lt;p&gt;" rather than a real "<p>" tag) — unescape entities first, then
    strip the resulting real tags. Confirmed live: without the unescape step,
    BeautifulSoup sees literal "&lt;p&gt;" text and leaves it untouched.

    get_text(separator="\\n") inserts a newline at every tag boundary, including
    inline ones like <strong>, which fragments sentences ("a \\ndriven\\n AI").
    Collapse those spurious single newlines to spaces while keeping genuine
    paragraph breaks (2+ consecutive newlines) intact — protect the paragraph
    breaks first, then collapse everything else."""
    unescaped = html_lib.unescape(raw or "")
    text = BeautifulSoup(unescaped, "html.parser").get_text(separator="\n")
    text = _PARAGRAPH_BREAK_RE.sub("\x00", text)  # protect real paragraph breaks
    text = text.replace("\n", " ")  # collapse spurious inline-tag newlines
    text = text.replace("\x00", "\n\n")
    return _SPACE_RUN_RE.sub(" ", text).strip()


def normalize_job(raw: dict, company: str) -> Posting:
    return Posting(
        source="greenhouse",
        id=str(raw["id"]),
        company=company,
        title=raw.get("title", ""),
        location=(raw.get("location") or {}).get("name", ""),
        department=(raw.get("departments") or [{}])[0].get("name") if raw.get("departments") else None,
        url=raw.get("absolute_url", ""),
        description=_strip_html(raw.get("content", "")),
        published_at=raw.get("first_published"),
    )


def fetch_postings(company: str, limit: int = 30, timeout: float = 15.0) -> list[Posting]:
    """Fetch up to `limit` current postings for a company's Greenhouse board."""
    with httpx.Client(timeout=timeout) as client:
        resp = client.get(f"{GREENHOUSE_BASE_URL}/{company}/jobs", params={"content": "true"})
        resp.raise_for_status()
        jobs = resp.json().get("jobs", [])[:limit]
    return [normalize_job(job, company) for job in jobs]


def fetch_postings_for_companies(companies: list[str], limit_per_company: int = 20, politeness_delay: float = 1.0) -> list[Posting]:
    """Fetch postings across multiple companies with a politeness delay between requests."""
    postings = []
    for i, company in enumerate(companies):
        try:
            postings.extend(fetch_postings(company, limit=limit_per_company))
        except httpx.HTTPStatusError as exc:
            print(f"[greenhouse] {company} failed: {exc}")
        if i < len(companies) - 1:
            time.sleep(politeness_delay)
    return postings
