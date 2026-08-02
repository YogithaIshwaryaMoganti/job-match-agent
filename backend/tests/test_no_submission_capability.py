"""Structural guardrail test: this codebase must never grow a function that
submits a job application to a real employer. This isn't a style nitpick —
it's the core safety property of the project (see docs/architecture.md). If
this test ever needs updating to allow a match, that's a decision requiring
explicit human sign-off, not something that should slip in silently.
"""

import re
from pathlib import Path

FORBIDDEN_PATTERNS = [
    r"submit_application",
    r"apply_to_job",
    r"auto_apply",
    r"post_application",
    r"submit_job_application",
]

SOURCE_ROOT = Path(__file__).parents[1] / "job_match_agent"


def test_no_forbidden_submission_function_names():
    combined_pattern = re.compile("|".join(FORBIDDEN_PATTERNS), re.IGNORECASE)
    offending = []
    for py_file in SOURCE_ROOT.rglob("*.py"):
        text = py_file.read_text()
        if combined_pattern.search(text):
            offending.append(str(py_file))
    assert offending == [], f"Found forbidden submission-related code in: {offending}"
