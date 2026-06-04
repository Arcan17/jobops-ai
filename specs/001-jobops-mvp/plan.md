# Implementation Plan: JobOps AI — MVP

**Branch**: `001-jobops-mvp` | **Date**: 2026-06-04 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/001-jobops-mvp/spec.md`

## Summary

Build a single-user, AI-powered job-search CRM backend. Core flow: maintain a candidate profile →
paste a structured job → compute a **defensible, deterministic hybrid fit score** (weighted
components, embedding-based stack/project matching; LLM only for narrative) → save as an
application and track it through a status board → generate a recruiter outreach message. The
engineering centerpiece is the reproducible hybrid scoring engine, fully testable under mock
providers with zero network calls in CI. Architecture and conventions are reused directly from the
existing AgentDesk AI project.

## Technical Context

**Language/Version**: Python 3.11+

**Primary Dependencies**: FastAPI, SQLAlchemy 2.0 (async), Pydantic v2, Alembic, structlog,
python-jose (JWT), passlib (hashing), httpx (tests), pytest + pytest-asyncio. Optional frontend:
Next.js 15 + TypeScript (thin board view; may be deferred).

**Storage**: PostgreSQL 16 + pgvector (single DB). Tests run on SQLite in-memory with an in-Python
cosine fallback for embedding similarity.

**Testing**: pytest (`asyncio_mode=auto`), deterministic mock LLM/embedding providers forced via
`LLM_PROVIDER=mock` / `EMBEDDING_PROVIDER=mock`.

**Target Platform**: Linux server (Docker Compose locally; Railway/Render for deploy).

**Project Type**: Web service (backend-first) with optional thin frontend.

**Performance Goals**: Not latency-critical; scoring a job is a single request returning in well
under 1s with mock providers. Demo flow completes in < 1 minute.

**Constraints**: Zero real LLM/embedding calls in CI; numeric score never produced by an LLM;
reproducible scores under the mock provider; all writes JWT-gated.

**Scale/Scope**: Single user, hundreds of job opportunities. ~8 entities, ~5 routers, one scoring
service as the centerpiece.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Compliance in this plan |
|---|---|
| I. Clean, Modular Architecture | api → services → models with cross-cutting `providers`; routers thin. PASS |
| II. Providers Behind Interfaces | `providers/` (base/factory/mock/anthropic/openai) copied from AgentDesk; mock default. PASS |
| III. Defensible, Deterministic Scoring | `scoring_service` computes number from weighted deterministic components; LLM only for narrative; reproducibility test required. PASS |
| IV. Deterministic Tests, No Paid APIs in CI | conftest forces mock; SQLite + Python cosine fallback; CI sets mock env. PASS |
| V. Security & Secret Hygiene | JWT (single seeded user), Pydantic v2 validation, `.env.example`, no secrets committed. PASS |
| VI. Observability & Explainability | structlog events; Score persists full component breakdown. PASS |

No violations → Complexity Tracking not required.

## Project Structure

### Documentation (this feature)

```text
specs/001-jobops-mvp/
├── plan.md              # This file
├── spec.md              # Feature specification (+ Clarifications)
├── research.md          # Phase 0 — decisions & rationale
├── data-model.md        # Phase 1 — entities & relationships
├── quickstart.md        # Phase 1 — how to run & demo
├── contracts/
│   └── openapi.md       # Phase 1 — endpoint contracts (summary)
└── tasks.md             # Phase 2 — created by /speckit-tasks
```

### Source Code (repository root)

```text
backend/
├── app/
│   ├── core/            # config.py (pydantic-settings), security.py (JWT), deps.py, logging.py
│   ├── api/v1/          # thin routers: health, auth, profile, jobs, applications, messages
│   │   └── router.py    # aggregates routers
│   ├── services/        # profile_service, scoring_service (CENTERPIECE), matching_service,
│   │                    # message_service, application_service
│   ├── models/          # profile, skill, project, job_opportunity, score, application,
│   │                    # application_event, generated_message
│   ├── schemas/         # Pydantic v2 request/response models
│   ├── providers/       # base, factory, mock, anthropic, openai  (copied from AgentDesk)
│   ├── db/              # engine.py, session.py, base.py (UUIDMixin, TimestampMixin), types.py (Embedding)
│   ├── scoring/         # weights.py (constants), components.py (per-factor deterministic fns)
│   ├── seed.py          # seed the single user + (optional) sample profile
│   └── main.py          # FastAPI app factory
├── tests/
│   ├── conftest.py      # mock env + sqlite in-memory + ASGITransport client (from AgentDesk)
│   ├── test_auth.py
│   ├── test_profile.py
│   ├── test_jobs.py
│   ├── test_scoring.py        # reproducibility + breakdown reconciliation (KEY)
│   ├── test_messages.py
│   └── test_applications.py
├── alembic/             # migrations
├── pyproject.toml       # deps + pytest/ruff/mypy config
├── Dockerfile
└── .env.example

docker-compose.yml       # db (pgvector/pg16) + backend (+ frontend profile)
.github/workflows/ci.yml # ruff + mypy + alembic + pytest (mock providers)
README.md                # professional README + architecture + demo
docs/adr/                # ADRs (hybrid scoring, provider abstraction, single-user auth)
frontend/                # OPTIONAL thin Next.js board (may be deferred to a follow-up)
```

**Structure Decision**: Backend-first web service mirroring AgentDesk AI's layout for consistency
and reuse. A dedicated `scoring/` package isolates the deterministic weighted components from the
`scoring_service` orchestration so the math is unit-testable in isolation. Frontend is optional for
v1; the API + tests are the acceptance surface.

## Reuse Map (from AgentDesk AI)

Copy and adapt from `/Users/bastian/Documents/agentdesk-ai/backend/`:

- `app/providers/*` → as-is (drop ticket-specific mock text; keep deterministic hash embeddings).
- `app/core/config.py`, `security.py`, `deps.py`, `logging.py` → adapt settings (scoring weights,
  thresholds, single-user creds) and drop RBAC/multi-tenant.
- `app/db/base.py` (UUIDMixin, TimestampMixin), `app/db/types.py` (Embedding column) → as-is.
- `app/services/retrieval_service.py` → basis for `matching_service` (cosine, dual-dialect: pgvector
  `<=>` on PostgreSQL, in-Python cosine on SQLite).
- `tests/conftest.py` → as-is pattern (force mock env, sqlite in-memory, async client).
- `pyproject.toml`, `docker-compose.yml`, `.github/workflows/ci.yml`, `Dockerfile` → adapt names,
  drop Redis/Celery/worker services.
- `.specify` constitution structure → already adapted.

## Phased Implementation

1. **Phase A — Skeleton & infra**: pyproject, app factory, config, db base/session, providers
   (mock default), conftest, docker-compose, CI. Health endpoint + green empty test run.
2. **Phase B — Profile & auth**: models (Profile, Skill, Project), JWT + seed user, profile/skill/
   project endpoints, embeddings computed on skill/project create. Tests: auth, profile.
3. **Phase C — Jobs & scoring (centerpiece)**: JobOpportunity model + structured-input schema;
   `scoring/weights.py` + `scoring/components.py` (deterministic per-factor); `matching_service`
   (cosine); `scoring_service` orchestration; Score persistence with breakdown; LLM narrative via
   mock. Tests: jobs, scoring reproducibility + breakdown reconciliation + recommendation thresholds.
4. **Phase D — Applications & board**: Application + ApplicationEvent models, create-from-score,
   state machine + transitions, board grouped-by-state endpoint. Tests: applications.
5. **Phase E — Messages**: GeneratedMessage model, `message_service` (recruiter outreach via mock,
   references role + top projects), persist + retrieve. Tests: messages (deterministic).
6. **Phase F — Polish**: README, ADRs, `.env.example`, structured-log events wired, optional thin
   Next.js board. Final full test run + docker compose smoke.

Each phase closes with a summary, file list, how-to-test, and a passing test run for affected
modules (per constitution). A phase MUST NOT advance with critical errors open.

## Complexity Tracking

No constitution violations. Section intentionally empty.
