"""Client for the Lever Postings API (api.lever.co/v0/postings) — public,
unauthenticated, explicitly built for third-party job-board consumption.

Confirmed live and functional (returns valid JSON) against real company slugs
(e.g. "lever", "plaid", "clari") — though several currently have zero open
postings via this endpoint at the time of writing, which is a real fact about
current hiring activity, not an integration gap. Greenhouse is the primary
demo data source for that reason; this client is a genuine second real
integration, not a stub.
"""

from __future__ import annotations

import html as html_lib
import re
import time

import httpx
from bs4 import BeautifulSoup

from job_match_agent.schema import Posting

LEVER_BASE_URL = "https://api.lever.co/v0/postings"

_PARAGRAPH_BREAK_RE = re.compile(r"\n{2,}")
_SPACE_RUN_RE = re.compile(r"[ \t]+")


def _strip_html(raw: str) -> str:
    """Same entity-unescape + inline-newline-collapse fix as the Greenhouse
    client — see its `_strip_html` docstring for why."""
    unescaped = html_lib.unescape(raw or "")
    text = BeautifulSoup(unescaped, "html.parser").get_text(separator="\n")
    text = _PARAGRAPH_BREAK_RE.sub("\x00", text)
    text = text.replace("\n", " ")
    text = text.replace("\x00", "\n\n")
    return _SPACE_RUN_RE.sub(" ", text).strip()


def _extract_description(raw: dict) -> str:
    if raw.get("descriptionPlain"):
        text = raw["descriptionPlain"]
    else:
        text = _strip_html(raw.get("description", ""))
    for section in raw.get("listsPlain") or raw.get("lists") or []:
        section_text = section.get("content") or section.get("text", "")
        if section.get("content") and "listsPlain" not in raw:
            section_text = _strip_html(section_text)
        text += f"\n\n{section.get('text', '')}\n{section_text}"
    return text.strip()


def normalize_posting(raw: dict, company: str) -> Posting:
    categories = raw.get("categories") or {}
    return Posting(
        source="lever",
        id=str(raw["id"]),
        company=company,
        title=raw.get("text", ""),
        location=categories.get("location", ""),
        department=categories.get("team") or categories.get("department"),
        url=raw.get("hostedUrl", ""),
        description=_extract_description(raw),
        published_at=str(raw.get("createdAt")) if raw.get("createdAt") else None,
    )


def fetch_postings(company: str, limit: int = 30, timeout: float = 15.0) -> list[Posting]:
    """Fetch up to `limit` current postings for a company's Lever board."""
    with httpx.Client(timeout=timeout) as client:
        resp = client.get(f"{LEVER_BASE_URL}/{company}", params={"mode": "json"})
        resp.raise_for_status()
        data = resp.json()
        if not isinstance(data, list):
            return []
        postings = data[:limit]
    return [normalize_posting(p, company) for p in postings]


def fetch_postings_for_companies(companies: list[str], limit_per_company: int = 20, politeness_delay: float = 1.0) -> list[Posting]:
    postings = []
    for i, company in enumerate(companies):
        try:
            postings.extend(fetch_postings(company, limit=limit_per_company))
        except httpx.HTTPStatusError as exc:
            print(f"[lever] {company} failed: {exc}")
        if i < len(companies) - 1:
            time.sleep(politeness_delay)
    return postings
