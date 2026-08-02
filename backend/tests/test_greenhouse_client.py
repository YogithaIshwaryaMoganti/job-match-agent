from job_match_agent.greenhouse_client import normalize_job

RAW_JOB = {
    "id": 8027437,
    "title": "AI Implementation Manager, Service Management ",
    "location": {"name": "New York City"},
    "departments": [{"id": 345526, "name": "AI GTM"}],
    "absolute_url": "https://www.asana.com/jobs/apply/8027437",
    "content": "&lt;p&gt;We&#39;re seeking a &lt;strong&gt;driven&lt;/strong&gt; AI Strategist.&lt;/p&gt;",
    "first_published": "2026-06-25T13:22:28-04:00",
}


def test_normalize_job_strips_double_encoded_html():
    posting = normalize_job(RAW_JOB, "asana")
    assert posting.source == "greenhouse"
    assert posting.id == "8027437"
    assert posting.company == "asana"
    assert posting.location == "New York City"
    assert posting.department == "AI GTM"
    assert "<" not in posting.description
    assert "&lt;" not in posting.description
    assert "We're seeking a driven AI Strategist." in posting.description


def test_normalize_job_handles_missing_department():
    raw = {**RAW_JOB, "departments": []}
    posting = normalize_job(raw, "asana")
    assert posting.department is None


def test_dedup_key_format():
    posting = normalize_job(RAW_JOB, "asana")
    assert posting.dedup_key == "greenhouse:8027437"
