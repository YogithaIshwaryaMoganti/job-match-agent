from job_match_agent.agent.matcher import score_posting, score_postings
from job_match_agent.generation.llm_client import ModelTurn, ToolCall
from job_match_agent.profile import DEMO_PROFILE
from job_match_agent.schema import Posting

POSTING = Posting(
    source="greenhouse",
    id="1",
    company="acme",
    title="Senior Full-Stack Engineer",
    location="Remote",
    department="Engineering",
    url="https://example.com/1",
    description="Looking for a senior engineer with Python, React, and LLM experience.",
    published_at=None,
)


class FakeLLMClient:
    def __init__(self, turn: ModelTurn):
        self._turn = turn
        self.calls = 0

    def create_turn(self, system, messages, tools, max_tokens=1024):
        self.calls += 1
        return self._turn


def make_turn(score=85, category="strong", reasoning="Great overlap"):
    return ModelTurn(
        text="",
        tool_calls=[ToolCall(id="t1", name="submit_score", input={"score": score, "category": category, "reasoning": reasoning})],
        stop_reason="tool_use",
        input_tokens=100,
        output_tokens=20,
    )


def test_score_posting_parses_tool_call():
    llm = FakeLLMClient(make_turn(score=90, category="strong", reasoning="Strong Python/React overlap"))
    result = score_posting(DEMO_PROFILE, POSTING, llm)
    assert result.score == 90
    assert result.category == "strong"
    assert "overlap" in result.reasoning


def test_score_posting_defaults_when_no_tool_call():
    turn = ModelTurn(text="I don't know", tool_calls=[], stop_reason="end_turn", input_tokens=10, output_tokens=5)
    llm = FakeLLMClient(turn)
    result = score_posting(DEMO_PROFILE, POSTING, llm)
    assert result.score == 0
    assert result.category == "poor"


def test_score_postings_scores_each_once():
    llm = FakeLLMClient(make_turn())
    results = score_postings(DEMO_PROFILE, [POSTING, POSTING, POSTING], llm)
    assert len(results) == 3
    assert llm.calls == 3
