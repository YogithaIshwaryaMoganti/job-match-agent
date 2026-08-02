import os
import tempfile

import pytest

from job_match_agent.dedup_store import DedupStore
from job_match_agent.schema import Posting


def make_posting(id_: str) -> Posting:
    return Posting(
        source="greenhouse",
        id=id_,
        company="acme",
        title="Engineer",
        location="Remote",
        department=None,
        url="https://example.com",
        description="desc",
        published_at=None,
    )


@pytest.fixture
def store():
    with tempfile.TemporaryDirectory() as d:
        yield DedupStore(db_path=os.path.join(d, "test.db"))


def test_first_run_all_unseen(store):
    postings = [make_posting("1"), make_posting("2")]
    assert len(store.filter_unseen(postings)) == 2


def test_marked_postings_are_filtered_on_next_run(store):
    postings = [make_posting("1"), make_posting("2")]
    store.mark_seen(store.filter_unseen(postings))
    assert store.filter_unseen(postings) == []


def test_partial_overlap(store):
    store.mark_seen([make_posting("1")])
    postings = [make_posting("1"), make_posting("2")]
    unseen = store.filter_unseen(postings)
    assert [p.id for p in unseen] == ["2"]


def test_empty_input_returns_empty(store):
    assert store.filter_unseen([]) == []
