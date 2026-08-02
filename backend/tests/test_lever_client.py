from job_match_agent.lever_client import normalize_posting

RAW_POSTING = {
    "id": "abc-123",
    "text": "Senior Backend Engineer",
    "categories": {"location": "Remote", "team": "Platform"},
    "hostedUrl": "https://jobs.lever.co/example/abc-123",
    "descriptionPlain": "We are hiring a senior backend engineer.",
    "listsPlain": [{"text": "Requirements", "content": "5+ years experience"}],
    "createdAt": 1700000000000,
}


def test_normalize_posting_uses_plain_text_fields():
    posting = normalize_posting(RAW_POSTING, "example")
    assert posting.source == "lever"
    assert posting.id == "abc-123"
    assert posting.title == "Senior Backend Engineer"
    assert posting.location == "Remote"
    assert posting.department == "Platform"
    assert "We are hiring" in posting.description
    assert "5+ years experience" in posting.description


def test_normalize_posting_handles_missing_categories():
    raw = {**RAW_POSTING, "categories": {}}
    posting = normalize_posting(raw, "example")
    assert posting.location == ""
    assert posting.department is None
