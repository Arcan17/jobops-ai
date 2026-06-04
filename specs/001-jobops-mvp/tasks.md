---
description: "Task list for JobOps AI MVP implementation"
---

# Tasks: JobOps AI — MVP

**Input**: Design documents from `/specs/001-jobops-mvp/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/openapi.md

**Tests**: REQUIRED — the spec mandates deterministic tests (Constitution IV). Test tasks are
included and, where marked, written before implementation.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: US1 (scoring), US2 (board), US3 (messages), US4 (profile/foundation)
- Paths are relative to repo root `/Users/bastian/Documents/jobops-ai/`.

---

## Phase 1: Setup (Shared Infrastructure)

- [ ] T001 Scaffold `backend/` structure per plan (app/{core,api/v1,services,models,schemas,providers,db,scoring}, tests/, alembic/).
- [ ] T002 Create `backend/pyproject.toml` (FastAPI, SQLAlchemy 2.0, asyncpg, aiosqlite, Pydantic v2, alembic, structlog, python-jose, passlib, httpx, pytest, pytest-asyncio, ruff, mypy) — adapt from AgentDesk.
- [ ] T003 [P] Configure ruff + mypy + pytest (`asyncio_mode=auto`) in pyproject.
- [ ] T004 [P] Add `backend/.env.example` (LLM_PROVIDER=mock, EMBEDDING_PROVIDER=mock, DATABASE_URL, SECRET_KEY, SEED_USER_EMAIL/PASSWORD, scoring weight overrides).
- [ ] T005 [P] Add `docker-compose.yml` (pgvector/pg16 + backend; drop redis/celery) and `backend/Dockerfile` — adapt from AgentDesk.
- [ ] T006 [P] Add `.github/workflows/ci.yml` (ruff → mypy → alembic upgrade → pytest, mock providers).

---

## Phase 2: Foundational (Blocking Prerequisites)

**⚠️ Must complete before user-story work.**

- [ ] T007 Copy/adapt `app/providers/{base,factory,mock,anthropic,openai}.py` from AgentDesk; mock default; strip ticket-specific text.
- [ ] T008 [P] Copy `app/db/{base.py (UUIDMixin, TimestampMixin), types.py (Embedding), engine.py, session.py}` from AgentDesk.
- [ ] T009 [P] Create `app/core/{config.py (pydantic-settings incl. scoring weights + thresholds), logging.py (structlog)}`.
- [ ] T010 Create `app/core/security.py` (JWT encode/decode) + `app/core/deps.py` (current-user dependency) — adapt from AgentDesk, drop RBAC.
- [ ] T011 Create `app/main.py` (FastAPI app factory) + `app/api/v1/router.py` + `app/api/v1/health.py` (`GET /health`).
- [ ] T012 Initialize Alembic; configure async migration env.
- [ ] T013 Copy `tests/conftest.py` pattern (force mock env, sqlite in-memory, ASGITransport client) from AgentDesk.
- [ ] T014 Verify foundation: empty/`test_health.py` passes; `docker compose up` serves `/docs`.

**Checkpoint**: Foundation ready.

---

## Phase 3: User Story 4 — Candidate profile (Priority: P1, foundational) 🎯

**Goal**: Persist profile, skills, projects (with embeddings) — basis for scoring.
**Independent Test**: Create/update profile + add skill/project, read back, all fields persist.

- [ ] T015 [US4] Models `app/models/{user,profile,skill,project}.py` per data-model.md (embeddings on skill/project).
- [ ] T016 [US4] Alembic migration for user/profile/skill/project tables.
- [ ] T017 [US4] Schemas `app/schemas/profile.py` (profile, skill, project request/response).
- [ ] T018 [US4] `app/services/profile_service.py` (CRUD; compute embeddings via EmbeddingProvider on skill/project create/update).
- [ ] T019 [US4] `app/api/v1/profile.py` router (GET/PUT profile; POST/DELETE skills; POST/DELETE projects).
- [ ] T020 [US4] `app/seed.py` (seed JWT user + optional sample profile) and `app/api/v1/auth.py` (`POST /auth/login`).
- [ ] T021 [P] [US4] Tests `tests/test_auth.py` (login returns JWT; writes rejected without token).
- [ ] T022 [P] [US4] Tests `tests/test_profile.py` (profile CRUD; skill/project create persists + embedding present).

**Checkpoint**: Profile + auth usable.

---

## Phase 4: User Story 1 — Hybrid scoring (Priority: P1) 🎯 CENTERPIECE

**Goal**: Paste structured job → reproducible 1–10 score + recommendation + breakdown + narrative.
**Independent Test**: POST job + score; assert score in [1,10], breakdown reconciles, reproducible.

- [ ] T023 [US1] Model `app/models/job_opportunity.py` + `app/models/score.py` (breakdown + narrative JSON) per data-model.md.
- [ ] T024 [US1] Alembic migration for job_opportunity + score.
- [ ] T025 [US1] Schemas `app/schemas/job.py` (structured job input) + `app/schemas/score.py` (breakdown, narrative, recommendation).
- [ ] T026 [P] [US1] `app/scoring/weights.py` (weights summing to 100 + recommendation thresholds, overridable from settings).
- [ ] T027 [US1] `app/services/matching_service.py` (cosine similarity, dual-dialect: pgvector `<=>` / in-Python fallback) adapted from AgentDesk retrieval_service.
- [ ] T028 [US1] `app/scoring/components.py` (deterministic per-factor fns: stack_match, seniority_match, modality_location, projects_match, salary_interest, risk_penalty).
- [ ] T029 [US1] `app/services/scoring_service.py` (orchestrate components → value+breakdown; recommendation from thresholds; LLM narrative via provider; persist Score).
- [ ] T030 [US1] `app/api/v1/jobs.py` router (POST/GET jobs, GET job detail, POST `/jobs/{id}/score`).
- [ ] T031 [P] [US1] Tests `tests/test_jobs.py` (create/list/get job; input validation).
- [ ] T032 [US1] Tests `tests/test_scoring.py` (KEY): reproducibility (same input → identical score), breakdown weighted-sum reconciles to value, weights sum to 100, recommendation thresholds (apply/apply_if_quick/skip), sparse-profile and missing-field cases.

**Checkpoint**: Scoring engine demonstrable and proven deterministic.

---

## Phase 5: User Story 2 — Application status board (Priority: P1)

**Goal**: Save scored job as application; move through states; view board grouped by state.
**Independent Test**: Create application, transition state, board reflects it, event persisted.

- [ ] T033 [US2] Models `app/models/{application,application_event}.py` + ApplicationState enum + transition map per data-model.md.
- [ ] T034 [US2] Alembic migration for application + application_event.
- [ ] T035 [US2] Schemas `app/schemas/application.py` (create, board card, state-change, metadata update).
- [ ] T036 [US2] `app/services/application_service.py` (create-from-score; validated state machine; record ApplicationEvent; board grouping).
- [ ] T037 [US2] `app/api/v1/applications.py` router (POST application, GET `/applications/board`, PATCH state, PATCH metadata).
- [ ] T038 [P] [US2] Tests `tests/test_applications.py` (create on board in `nueva`; valid transition records event; invalid transition → 422; board grouped in canonical order).

**Checkpoint**: Board usable end-to-end.

---

## Phase 6: User Story 3 — Recruiter message generation (Priority: P2)

**Goal**: Generate + persist a recruiter outreach message referencing role + top projects.
**Independent Test**: Generate message for an application; non-empty, references role; deterministic.

- [ ] T039 [US3] Model `app/models/generated_message.py` (type=recruiter_outreach, tone, content).
- [ ] T040 [US3] Alembic migration for generated_message.
- [ ] T041 [US3] `app/services/message_service.py` (build prompt from role + top-matching projects; LLM via provider; persist linked to application).
- [ ] T042 [US3] Extend `app/api/v1/applications.py` (POST/GET `/applications/{id}/messages`).
- [ ] T043 [P] [US3] Tests `tests/test_messages.py` (message references role; deterministic under mock; persisted + retrievable).

**Checkpoint**: Full demo flow works.

---

## Phase 7: Polish

- [ ] T044 [P] Wire structlog events (profile_updated, job_created, score_computed, message_generated, application_status_changed).
- [ ] T045 [P] `README.md` (problem, architecture, hybrid-scoring explainer, demo, CV blurb).
- [ ] T046 [P] ADRs in `docs/adr/` (hybrid scoring, provider abstraction, single-user JWT).
- [ ] T047 Final full `pytest` run (mock providers) + `docker compose up` smoke test of the demo flow via `/docs`.
- [ ] T048 [P] (Optional) Thin Next.js board reading `/applications/board`.

---

## Dependencies & Parallelization

- Phase 1 → Phase 2 → (Phase 3) → Phase 4 → Phase 5 → Phase 6 → Phase 7.
- US4 (profile) blocks US1 (scoring needs skills/projects). US1 blocks US2 (board attaches score)
  and US3 (message uses scored application context).
- `[P]` tasks within a phase touch different files and may run in parallel.
- KEY task T032 (scoring reproducibility + breakdown reconciliation) is the acceptance gate for
  the project's differentiator — do not mark US1 complete until it passes.
