"""Candidate profile schema. A real user would supply their own; the demo
profile here mirrors the portfolio's own positioning (senior full-stack +
hands-on agentic AI) so the eval fixtures and demo runs are self-consistent."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class CandidateProfile:
    name: str
    headline: str
    summary: str
    skills: list[str]
    years_experience: int
    target_titles: list[str]
    preferred_locations: list[str] = field(default_factory=lambda: ["Remote"])

    def to_prompt_text(self) -> str:
        return (
            f"Name: {self.name}\n"
            f"Headline: {self.headline}\n"
            f"Years of experience: {self.years_experience}\n"
            f"Skills: {', '.join(self.skills)}\n"
            f"Target roles: {', '.join(self.target_titles)}\n"
            f"Preferred locations: {', '.join(self.preferred_locations)}\n\n"
            f"Summary: {self.summary}"
        )


DEMO_PROFILE = CandidateProfile(
    name="Demo Candidate",
    headline="Senior Software Engineer — Full-Stack & Agentic AI Systems",
    summary=(
        "Senior software engineer with production experience across Java/Spring Boot, "
        "Python/FastAPI, and Next.js/React, now focused on hands-on agentic AI and LLM "
        "systems — retrieval pipelines, multi-turn tool-calling agents, and the evals/"
        "guardrails that make them production-ready. Comfortable owning a service "
        "end-to-end: backend, frontend, and the AI layer."
    ),
    skills=[
        "Java", "Spring Boot", "Python", "FastAPI", "TypeScript", "Next.js", "React",
        "LLM APIs", "Agentic tool-calling", "RAG", "Vector search", "OpenTelemetry",
        "PostgreSQL", "GCP", "Azure", "Docker",
    ],
    years_experience=6,
    target_titles=[
        "Senior Software Engineer", "Senior Full-Stack Engineer",
        "AI Engineer", "Machine Learning Engineer", "Applied AI Engineer",
    ],
    preferred_locations=["Remote", "New York City", "San Francisco, CA"],
)
