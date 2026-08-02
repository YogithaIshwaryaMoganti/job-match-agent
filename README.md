# Job Match & Shortlist Agent

Fetches real, live job postings from Greenhouse and Lever's public job-board APIs,
scores each against a candidate profile, and drafts a cover-letter opening for the
strongest matches. **It never submits an application to a real employer** — that's a
deliberate scope decision (see [`docs/architecture.md`](docs/architecture.md)), enforced
by a structural test that fails the build if any submission-shaped function is ever
added.

See [`docs/eval-report.md`](docs/eval-report.md) for eval numbers.

## Why this project

- **No scraping.** Sources exclusively from Greenhouse (`boards-api.greenhouse.io`) and
  Lever (`api.lever.co`) — official, public, documented APIs meant for third-party
  consumption. Not LinkedIn/Indeed, which have real legal precedent against scraping.
- **Draft, never submit.** A bot silently submitting applications under someone's name
  is a reputational risk, not just a nice-to-have missing feature. This agent stops at
  "ready for your review."
- **Real guardrails, not hypothetical ones.** A SQLite dedup store (tested: first run
  sees N unseen postings, second run sees 0) and a hard cap on postings scored per run —
  both verified, not just described.
- **Found and fixed a real data-quality bug** while building this: Greenhouse's job
  description field is HTML-entity-double-encoded; see the architecture doc for the fix.

## Current status

Same honest gap as project 2 (agentic-code-review-bot) — this project's core mechanic
(LLM-based fit scoring) has no meaningful signal without a live LLM call. Verified
without any API key:
- Greenhouse client confirmed live against 6 real companies (180-548 postings each);
  Lever client confirmed live and functional.
- Dedup store logic verified with real SQLite behavior.
- Matching/drafting logic verified deterministically via fake LLM clients
  (threshold filtering, defaulting behavior on missing tool calls).
- The "never submits" guarantee is enforced by a structural source-scan test, not just
  documented intent.
- Backend/frontend build/lint/typecheck/tests all clean; `/shortlist` correctly 503s
  without a key.

Pending a personal `ANTHROPIC_API_KEY`: real classification-accuracy numbers on the
18-posting golden set.

## Stack

**Backend:** Python, FastAPI, SQLite (dedup), Anthropic Claude, OpenTelemetry.
**Frontend:** Next.js, React.
**Data:** Greenhouse Job Board API, Lever Postings API — both public, read-only.

## Running it locally

### Backend

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

cp ../.env.example .env
# Edit .env — add your OWN personal Anthropic API key (console.anthropic.com).

pytest                     # unit tests — no live API needed
python -m evals.run_evals  # eval harness → docs/eval-report.md (needs the key)

uvicorn job_match_agent.app.main:app --reload --port 8422
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:3000 and click "Run shortlist."

## API

- `GET /health`
- `POST /shortlist` — fetches, dedups, scores, and drafts for the demo profile;
  returns the ranked shortlist + a disclaimer that nothing was submitted.

## Project layout

```
docs/                              architecture.md, eval-report.md
backend/job_match_agent/
  greenhouse_client.py              real Greenhouse Job Board API
  lever_client.py                   real Lever Postings API
  dedup_store.py                    SQLite seen-postings tracker
  profile.py                        candidate profile schema + demo profile
  agent/matcher.py                  fit scoring per posting
  agent/drafter.py                  cover-letter drafting (drafts only)
  pipeline.py                       fetch → dedup → score → draft orchestration
backend/tests/                     unit tests, incl. a structural no-submission guardrail
backend/evals/                     18 hand-labeled real postings (frozen) + eval runner
frontend/                          Next.js dashboard
```

## License

MIT
