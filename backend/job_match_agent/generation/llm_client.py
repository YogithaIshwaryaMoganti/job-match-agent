"""Provider-agnostic LLM interface. Uses the same tool-call-for-structured-output
trick as the other two portfolio projects (a `submit_*` tool the model calls
exactly once) rather than parsing free text — reliable, schema-validated output
without a full multi-turn agent loop, since this project's matching step is a
single-shot classification/scoring call per posting, not multi-turn investigation.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any, Protocol


@dataclass
class ToolCall:
    id: str
    name: str
    input: dict


@dataclass
class ModelTurn:
    text: str
    tool_calls: list[ToolCall]
    stop_reason: str
    input_tokens: int
    output_tokens: int
    raw_content: list[dict] = field(default_factory=list)


class LLMClient(Protocol):
    def create_turn(
        self, system: str, messages: list[dict[str, Any]], tools: list[dict], max_tokens: int = 1024
    ) -> ModelTurn: ...


class AnthropicLLMClient:
    def __init__(self, model: str = "claude-sonnet-4-5", api_key: str | None = None):
        import anthropic

        api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise RuntimeError(
                "ANTHROPIC_API_KEY is not set. Copy .env.example to .env and add your "
                "own personal Anthropic API key (console.anthropic.com)."
            )
        self._client = anthropic.Anthropic(api_key=api_key)
        self._model = model

    def create_turn(
        self, system: str, messages: list[dict[str, Any]], tools: list[dict], max_tokens: int = 1024
    ) -> ModelTurn:
        response = self._client.messages.create(
            model=self._model,
            max_tokens=max_tokens,
            system=system,
            messages=messages,
            tools=tools,
        )
        text_parts = [block.text for block in response.content if block.type == "text"]
        tool_calls = [
            ToolCall(id=block.id, name=block.name, input=block.input)
            for block in response.content
            if block.type == "tool_use"
        ]
        return ModelTurn(
            text="".join(text_parts),
            tool_calls=tool_calls,
            stop_reason=response.stop_reason,
            input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens,
            raw_content=[block.model_dump() for block in response.content],
        )


def get_llm_client() -> LLMClient:
    provider = os.environ.get("LLM_PROVIDER", "anthropic").lower()
    if provider == "anthropic":
        return AnthropicLLMClient(model=os.environ.get("LLM_MODEL", "claude-sonnet-4-5"))
    raise ValueError(f"Unsupported LLM_PROVIDER: {provider}")
