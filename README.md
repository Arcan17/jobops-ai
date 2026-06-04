# JobOps AI — AI-powered Job Search CRM

> Score jobs, generate outreach, track applications — with a **defensible, reproducible**
> AI scoring engine, not a black-box chatbot.

JobOps AI is a single-user job-search CRM. You keep a candidate profile (skills, projects,
preferences); you paste a job opportunity; the system scores the fit against your profile with a
**hybrid algorithm** (deterministic weighted components + embeddings, LLM only for narrative),
recommends whether to apply, generates a recruiter outreach message, and tracks the application
through a status board.

## Why it's different

Most "AI job tools" ask an LLM for a number. That's non-deterministic and untestable. JobOps AI
computes the score from **explicit, weighted, deterministic components** and only uses the LLM to
*explain* the result — never to set the number. The same profile + job always produces the same
score, and a test asserts it.

## The hybrid scoring engine

The 1–10 score is `1 + 9 × Σ(weightᵢ/100 × sub_scoreᵢ)`, with weights summing to 100:

| Factor | Weight | How it's computed |
|---|---:|---|
| `stack_match` | 30 | mean top-k cosine similarity between job stack/requirements and your skills (embeddings) |
| `seniority_match` | 20 | rule: exact = 1.0, ±1 level = 0.6, else 0.2 |
| `modality_location` | 15 | rule: modality + location/remote compatibility |
| `projects_match` | 15 | max cosine similarity between the job and your projects (embeddings) |
| `salary_interest` | 10 | rule: meets expectation = 1.0, within 20% = 0.7, unknown = 0.5 |
| `risk_penalty` | 10 | starts at 1.0; each detected blocker (e.g. on-site, clearance) subtracts 0.25 |

The recommendation is derived deterministically: **apply** (≥ 7), **apply if quick** (5–6.9),
**skip** (< 5). Every score persists its full component breakdown so any recommendation is
explainable after the fact.

## Stack

Python 3.11 · FastAPI · SQLAlchemy 2.0 (async) · PostgreSQL 16 + pgvector · Pydantic v2 ·
JWT auth · structlog · pytest · Docker · GitHub Actions. LLM/embeddings sit behind a provider
abstraction (Mock / Anthropic / OpenAI); **Mock is the default and the only provider used in CI**.

## Architecture

```
api (routers, thin)  →  services (business logic)  →  models (async ORM)
                      ↘  scoring/ (weights + deterministic components)
                      ↘  providers/ (LLM + embeddings behind interfaces)
```

Routers contain no business logic. No vendor SDK is imported outside `providers/`. The numeric
score is never produced by an LLM. See [the constitution](.specify/memory/constitution.md) and
[ADRs](docs/adr/).

## Quickstart

```bash
cp backend/.env.example backend/.env   # set a JWT_SECRET; mock providers are the default
docker compose up --build              # Postgres+pgvector + backend on :8000
# open http://localhost:8000/docs
```

The backend container runs migrations and seeds a single user (`SEED_USER_EMAIL` /
`SEED_USER_PASSWORD`) on startup.

### Frontend (Next.js board)

```bash
cd frontend
cp .env.local.example .env.local   # point NEXT_PUBLIC_API_URL at the backend
npm install
npm run dev                        # http://localhost:3000
```

A dark-themed dashboard: sign in, paste a job, score it (with the component breakdown
visualized), add it to the board, move applications through states, and generate the recruiter
message. Next.js 15 (App Router) · TypeScript · Tailwind v4.

### Demo flow (under a minute)

1. `POST /api/v1/auth/login` → copy the `access_token`.
2. `PUT /api/v1/profile` + add skills/projects (or use the seeded sample profile).
3. `POST /api/v1/jobs` with a structured job payload.
4. `POST /api/v1/jobs/{id}/score` → 1–10 score, recommendation, component breakdown, narrative.
5. `POST /api/v1/applications` → the job lands on the board in `nueva`.
6. `POST /api/v1/applications/{id}/messages` → generate the recruiter message.
7. `PATCH /api/v1/applications/{id}/state` → move it through the board; `GET /applications/board`.

## Tests (deterministic, no network)

```bash
cd backend
python3.11 -m venv .venv && . .venv/bin/activate
pip install -e ".[dev]"
ruff check app tests && mypy app
LLM_PROVIDER=mock EMBEDDING_PROVIDER=mock pytest -q
```

The key suite, `tests/test_scoring.py`, asserts the score is reproducible and that the breakdown's
weighted sum reconciles to the final value.

## Recruiter safety check

Paste a recruiter message and get a **deterministic, rule-based** risk read (green / yellow /
orange / red) with the specific signals that fired — asks for documents, upfront fee, move to
WhatsApp/Telegram, free-email domain, no official link, no company named, urgency, generic
greeting. Like the score, the verdict is a function of weighted signals, never an LLM guess, and
it's framed as *indicators to verify* with a concrete next-step recommendation — not an accusation.
Endpoint: `POST /api/v1/safety/check`.

## Roadmap

- **v1 (this repo)**: profile, hybrid scoring, recruiter message, application board, recruiter
  safety check.
- **v2**: RAG over your CV, interview prep, Kanban, CSV export, email reminders.
- **v3**: Gmail/Calendar integration, job import, browser extension, multi-user SaaS.

## Spec-driven

Built with [Spec Kit](https://github.com/github/spec-kit): constitution → spec → clarify → plan →
tasks → analyze → implement. Artifacts live in [`specs/001-jobops-mvp/`](specs/001-jobops-mvp/).
