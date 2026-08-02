"""Unified job posting schema that Greenhouse and Lever records normalize into."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Posting:
    source: str  # "greenhouse" or "lever"
    id: str
    company: str
    title: str
    location: str
    department: str | None
    url: str
    description: str  # plain text, HTML stripped
    published_at: str | None

    @property
    def dedup_key(self) -> str:
        return f"{self.source}:{self.id}"
