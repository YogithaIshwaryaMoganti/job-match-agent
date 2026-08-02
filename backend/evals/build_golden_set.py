"""One-time (rerunnable) generator for evals/golden_set.jsonl.

Fetches real, live job postings from Greenhouse and freezes a hand-picked,
hand-labeled subset (18 postings spanning strong/possible/poor fit against
DEMO_PROFILE) into the golden set with their FULL content at build time.

Deliberately frozen, unlike project 1's golden set (which re-fetches CVEs by
ID at eval time — CVE records are permanent public data). Job postings are
NOT permanent: they get filled or taken down, so re-fetching by ID later
would make the eval non-reproducible or silently drop cases. Freezing today's
real content is the correct choice here.

Run with: python -m evals.build_golden_set
"""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from job_match_agent.greenhouse_client import fetch_postings

OUTPUT_PATH = Path(__file__).parent / "golden_set.jsonl"

# (company, posting_id, expected_category) — hand-picked from a live fetch on
# 2026-08-02, spanning clear strong/possible/poor fits against DEMO_PROFILE
# (senior full-stack + agentic AI engineer, 6 yrs experience, IC-track).
LABELED_POSTINGS = [
    ("stripe", "8062305", "strong"),  # Full Stack Engineer, Link
    ("stripe", "8044460", "strong"),  # AI Engineer
    ("asana", "7978649", "strong"),  # Senior Software Engineer, AI Retrieval
    ("asana", "7964335", "strong"),  # Senior Software Engineer, AI Developer Experience
    ("coinbase", "8051871", "strong"),  # Senior SWE, Backend - Core AI Automation
    ("robinhood", "8008723", "strong"),  # Full Stack Software Engineer, Credit Cards & Banking
    ("pinterest", "5459622", "possible"),  # Software Engineer II, Full Stack (seniority stretch below)
    ("airbnb", "7955579", "possible"),  # Principal ML Engineer, LLM Fine-tuning (seniority stretch above + research-heavy)
    ("pinterest", "7305880", "possible"),  # Staff Software Engineer, AI Tools (seniority stretch above)
    ("coinbase", "8070574", "possible"),  # Senior SWE, Frontend (Agentic Trading) — frontend-only, domain match
    ("robinhood", "7960680", "possible"),  # Machine Learning Engineer — classical ML, not profile's agentic/app-AI focus
    ("asana", "7586942", "possible"),  # Senior Engineering Manager, AI Agents — management track
    ("stripe", "7954688", "poor"),  # Account Executive, AI Sales — not engineering
    ("asana", "7766762", "poor"),  # Junior Software Engineer — seniority mismatch
    ("pinterest", "6922682", "poor"),  # Software Engineer, iOS — mobile specialist, no overlap
    ("pinterest", "8010903", "poor"),  # Manager II, Machine Learning - Conversion Visibility — people management + narrow domain
    ("coinbase", "7652048", "poor"),  # Software Engineer - Salesforce Platform — unrelated stack
    ("robinhood", "7648454", "poor"),  # Senior Software Engineer, Cloud Integration — narrow infra niche, no stack overlap
]


def build() -> None:
    needed_by_company: dict[str, set[str]] = {}
    for company, posting_id, _ in LABELED_POSTINGS:
        needed_by_company.setdefault(company, set()).add(posting_id)

    frozen = {}
    for company, ids in needed_by_company.items():
        print(f"Fetching {company} (need {len(ids)} specific postings)...")
        postings = fetch_postings(company, limit=200, timeout=40.0)
        for p in postings:
            if p.id in ids:
                frozen[(company, p.id)] = p

    missing = [(c, i) for c, i, _ in LABELED_POSTINGS if (c, i) not in frozen]
    if missing:
        print(f"WARNING: {len(missing)} labeled postings not found (may have been filled/removed): {missing}")

    entries = []
    for company, posting_id, category in LABELED_POSTINGS:
        posting = frozen.get((company, posting_id))
        if posting is None:
            continue
        entries.append({"posting": asdict(posting), "expected_category": category})

    with open(OUTPUT_PATH, "w") as f:
        f.writelines(json.dumps(e) + "\n" for e in entries)

    print(f"Wrote {len(entries)}/{len(LABELED_POSTINGS)} golden entries to {OUTPUT_PATH}")


if __name__ == "__main__":
    build()
