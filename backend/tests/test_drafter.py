from job_match_agent.agent.drafter import draft_for_top_matches
from job_match_agent.agent.matcher import MatchResult
from job_match_agent.generation.llm_client import ModelTurn
from job_match_agent.profile import DEMO_PROFILE
from job_match_agent.schema import Posting


def make_match(score: int, key: str) -> MatchResult:
    posting = Posting(
        source="greenhouse", id=key, company="acme", title="Engineer", location="Remote",
        department=None, url="https://example.com", description="desc", published_at=None,
    )
    return MatchResult(posting=posting, score=score, category="strong", reasoning="x", input_tokens=1, output_tokens=1)


class FakeLLMClient:
    def create_turn(self, system, messages, tools, max_tokens=1024):
        return ModelTurn(text="Draft paragraph here.", tool_calls=[], stop_reason="end_turn", input_tokens=50, output_tokens=30)


def test_only_drafts_for_matches_above_threshold():
    matches = [make_match(90, "1"), make_match(60, "2"), make_match(75, "3")]
    drafts = draft_for_top_matches(DEMO_PROFILE, matches, FakeLLMClient(), score_threshold=75)
    assert set(drafts.keys()) == {"greenhouse:1", "greenhouse:3"}


def test_no_drafts_when_nothing_meets_threshold():
    matches = [make_match(40, "1"), make_match(50, "2")]
    drafts = draft_for_top_matches(DEMO_PROFILE, matches, FakeLLMClient(), score_threshold=75)
    assert drafts == {}
