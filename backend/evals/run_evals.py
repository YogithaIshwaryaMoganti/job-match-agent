"""Eval harness: measures classification accuracy of the matching agent against
18 hand-labeled real postings (frozen at build time — see build_golden_set.py
for why). No fallback tier exists here either — needs a live LLM key.

Run with: python -m evals.run_evals
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path

from dotenv import load_dotenv

from job_match_agent.agent.matcher import score_posting
from job_match_agent.generation.llm_client import get_llm_client
from job_match_agent.profile import DEMO_PROFILE
from job_match_agent.schema import Posting

load_dotenv()

GOLDEN_SET_PATH = Path(__file__).parent / "golden_set.jsonl"
REPORTS_DIR = Path(__file__).parent / "reports"
DOCS_REPORT_PATH = Path(__file__).parents[2] / "docs" / "eval-report.md"

# Adjacent categories (e.g. calling a "possible" posting "strong") count as a
# partial miss, not a full miss — the eval report distinguishes exact accuracy
# from "within one category" agreement, which is the more forgiving but still
# meaningful bar for a subjective fit judgment.
CATEGORY_ORDER = {"poor": 0, "possible": 1, "strong": 2}


def load_golden_set() -> list[dict]:
    entries = []
    with open(GOLDEN_SET_PATH) as f:
        for line in f:
            if not line.strip():
                continue
            d = json.loads(line)
            entries.append({"posting": Posting(**d["posting"]), "expected_category": d["expected_category"]})
    return entries


def run_all() -> dict:
    golden_set = load_golden_set()
    llm = get_llm_client()

    exact_matches = 0
    within_one = 0
    per_item = []

    for entry in golden_set:
        result = score_posting(DEMO_PROFILE, entry["posting"], llm)
        expected = entry["expected_category"]
        exact = result.category == expected
        distance = abs(CATEGORY_ORDER.get(result.category, 0) - CATEGORY_ORDER.get(expected, 0))

        exact_matches += int(exact)
        within_one += int(distance <= 1)

        per_item.append(
            {
                "title": entry["posting"].title,
                "company": entry["posting"].company,
                "expected": expected,
                "predicted": result.category,
                "score": result.score,
                "exact_match": exact,
            }
        )

    n = len(golden_set)
    return {
        "n": n,
        "exact_accuracy": round(exact_matches / n, 3),
        "within_one_category_accuracy": round(within_one / n, 3),
        "per_item": per_item,
    }


def write_markdown_report(results: dict | None, timestamp: str) -> None:
    if results is None:
        DOCS_REPORT_PATH.write_text(
            "# Eval Report\n\n"
            f"Generated: {timestamp}\n\n"
            "_Skipped — ANTHROPIC_API_KEY not set. No fallback tier exists for this "
            "project's core mechanic either. 18 hand-labeled real postings (frozen "
            "2026-08-02) are ready in evals/golden_set.jsonl.\n"
        )
        return

    lines = [
        "# Eval Report",
        "",
        f"Generated: {timestamp}",
        "",
        "## Matching agent classification accuracy",
        "",
        f"- Golden set: {results['n']} real postings (frozen 2026-08-02), hand-labeled strong/possible/poor",
        f"- Exact category accuracy: **{results['exact_accuracy']}**",
        f"- Within-one-category accuracy: **{results['within_one_category_accuracy']}**",
        "",
        (
            "(\"Within one category\" counts calling a 'possible' fit 'strong' as a partial "
            "miss rather than a full miss — fit judgment is inherently somewhat subjective; "
            "exact accuracy is the stricter, primary number.)"
        ),
        "",
    ]
    DOCS_REPORT_PATH.write_text("\n".join(lines))


def main() -> None:
    timestamp = time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime()) + "Z"

    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("ANTHROPIC_API_KEY not set — cannot run this eval harness (no fallback tier for this project).")
        write_markdown_report(None, timestamp)
        return

    results = run_all()
    print(json.dumps({k: v for k, v in results.items() if k != "per_item"}, indent=2))

    REPORTS_DIR.mkdir(exist_ok=True)
    report_path = REPORTS_DIR / f"{timestamp.replace(':', '')}.json"
    report_path.write_text(json.dumps(results, indent=2))
    write_markdown_report(results, timestamp)
    print(f"\nReport written to {report_path} and {DOCS_REPORT_PATH}")


if __name__ == "__main__":
    main()
