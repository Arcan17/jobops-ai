<!--
SYNC IMPACT REPORT
==================
Version change: (none) → 1.0.0
Bump rationale: Initial ratification of the JobOps AI constitution (first concrete
                version replacing the unfilled template).
Modified principles: N/A (initial definition)
Added sections:
  - Core Principles (I–VI)
  - Additional Constraints: Technology & Security Standards
  - Development Workflow & Quality Gates
  - Governance
Removed sections: none
Templates requiring updates:
  - .specify/templates/plan-template.md ✅ reviewed (Constitution Check gate aligns)
  - .specify/templates/spec-template.md ✅ reviewed (no mandated section conflicts)
  - .specify/templates/tasks-template.md ✅ reviewed (testing/observability task types covered)
Deferred TODOs: none
-->

# JobOps AI Constitution

JobOps AI is an AI-powered job-search CRM. A candidate pastes a job opportunity, the system
scores it against their profile with a defensible hybrid algorithm, recommends whether to apply,
generates a recruiter message, and tracks the application through a status board. This
constitution defines the non-negotiable engineering principles for the project. It exists to keep
the codebase clean, secure, deterministic, and demonstrably production-grade for a professional
portfolio. The MVP is intentionally single-user; multi-tenant SaaS is explicitly out of scope for
v1.

## Core Principles

### I. Clean, Modular Architecture
The system MUST maintain strict separation of concerns across layers:
`api` (HTTP routing + I/O schemas) → `services` (business logic) → `models` (persistence) with a
cross-cutting `providers` layer (LLM/embeddings). Business logic MUST NOT live in route handlers.
Modules MUST depend inward only; a model never imports a router. Rationale: a recruiter or
engineer must navigate the codebase and locate any responsibility in seconds, and layers must be
independently testable.

### II. Providers Behind Interfaces (NON-NEGOTIABLE)
All LLM and embedding access MUST go through abstract interfaces (`LLMProvider`,
`EmbeddingProvider`). Concrete adapters (Anthropic, OpenAI, Mock) are selected by environment
variable. A deterministic `MockProvider` is the default and the ONLY provider exercised in tests
and CI. No business code may import a vendor SDK directly. Rationale: vendor lock-in is avoided,
costs are controlled, and the system is testable without network or paid APIs.

### III. Defensible, Deterministic Scoring (NON-NEGOTIABLE)
The job-fit score MUST be computed by a hybrid algorithm, never by asking an LLM for a number.
The numeric score (1–10) MUST be derived from explicit, weighted, deterministic components:
stack match (embedding/cosine similarity), seniority match, modality/location, salary/interest,
relevant-projects match, and risk/blocker penalties. The LLM (mock by default) is used ONLY for
qualitative narrative (risk explanation, projects to highlight, rationale text) and MUST NOT
alter the number. Given the same profile and job input under the mock provider, the score MUST be
reproducible byte-for-byte. Rationale: a reproducible, explainable score is the project's core
engineering differentiator and the thing a technical reviewer will scrutinize.

### IV. Deterministic Tests, No Paid APIs in CI (NON-NEGOTIABLE)
Tests MUST be deterministic and reproducible. There MUST be zero real LLM/embedding calls in CI;
the mock provider is forced via `LLM_PROVIDER=mock` and `EMBEDDING_PROVIDER=mock`. Every feature
ships with tests covering its happy path and key failure modes. Required coverage areas: profile
management, job creation/parsing, hybrid scoring (reproducibility + component weights), message
generation (mock), and application status transitions. Rationale: CI must be free, fast, and
never flaky due to external services.

### V. Security & Secret Hygiene (NON-NEGOTIABLE)
Secrets MUST NEVER be hardcoded or committed; a complete `.env.example` documents every variable.
All external inputs MUST be validated with Pydantic v2. Even in single-user mode the API MUST
gate write access behind a simple auth token/JWT. Errors MUST be handled and never leak stack
traces or secrets to clients. Rationale: the project must model real production security posture
even at MVP scale.

### VI. Observability & Explainability
The system MUST emit structured logs for key events (`profile_updated`, `job_created`,
`score_computed`, `message_generated`, `application_status_changed`). Every computed score MUST
persist its component breakdown (per-factor sub-scores and weights), not just the final number,
so any recommendation can be explained after the fact. Rationale: scoring and AI output are only
trustworthy when measurable and traceable.

## Additional Constraints: Technology & Security Standards

- Backend: Python 3.11+, FastAPI, SQLAlchemy 2.0 (async), Pydantic v2, Alembic migrations.
- Data: PostgreSQL 16 with the pgvector extension as the vector store (single database). Tests
  may run against SQLite in-memory with an in-Python cosine fallback for embedding similarity.
- LLM/embeddings: provider abstraction with Mock (default), Anthropic, and OpenAI adapters.
- Frontend (if included in v1): Next.js 15 with TypeScript; a status board listing applications
  by state (no drag-and-drop Kanban required for v1).
- Infrastructure: Docker Compose MUST bring up the stack locally (postgres+pgvector, backend, and
  frontend if present).
- CI/CD: GitHub Actions running lint (ruff), type-check (mypy), Alembic migrations, and pytest
  with mock providers only.
- Out of scope for v1 (deferred): Celery/Redis async jobs, RAG over CV, interview prep, recruiter
  safety check, multi-tenant SaaS, scraping/import, email reminders, calendar/Gmail integrations.

## Development Workflow & Quality Gates

- Spec-driven development is mandatory: specify → clarify → plan → tasks → analyze → implement.
- Implementation proceeds in phases; a phase MUST NOT advance while critical errors remain.
- Each phase closes with: a summary of changes, the list of files created/modified, how to test
  it, and a passing test run for the affected modules.
- New behavior requires accompanying deterministic tests (Principle IV).
- Code MUST be reasonably typed and endpoints documented (FastAPI/OpenAPI).
- No change may introduce a direct vendor SDK import outside the `providers` layer (Principle II),
  a hardcoded secret (Principle V), or an LLM-produced numeric score (Principle III).

## Governance

This constitution supersedes ad-hoc practices for JobOps AI. Amendments MUST be made by editing
this file, accompanied by a Sync Impact Report and a semantic version bump:
- MAJOR: removal or backward-incompatible redefinition of a principle.
- MINOR: a new principle or materially expanded guidance.
- PATCH: clarifications and wording fixes.

All implementation work and reviews MUST verify compliance with these principles. Any deviation
MUST be justified in writing within the relevant spec or plan. Runtime development guidance for AI
agents lives in the project `CLAUDE.md`.

**Version**: 1.0.0 | **Ratified**: 2026-06-04 | **Last Amended**: 2026-06-04
