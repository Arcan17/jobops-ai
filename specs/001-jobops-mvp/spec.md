# Feature Specification: JobOps AI — MVP

**Feature Branch**: `001-jobops-mvp`

**Created**: 2026-06-04

**Status**: Draft

**Input**: User description: "JobOps AI MVP: paste a job, hybrid scoring, recruiter message, application status board"

## Overview

JobOps AI is a single-user, AI-powered job-search CRM. The candidate maintains a profile
(skills, projects, experience, preferences). They paste a job opportunity; the system scores the
fit against the profile using a **defensible hybrid algorithm** (deterministic weighted
components, not an LLM-produced number), recommends whether to apply, generates a recruiter
outreach message, and tracks the application through a status board. The MVP target is a flow
demonstrable in about one minute: **paste a job → see a reproducible score with breakdown →
generate a message → the application appears on the board**.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Score a pasted job against my profile (Priority: P1)

As a job-seeker with a configured profile, I paste a job opportunity (description, company,
stack, requirements, modality, location, salary if present) and immediately get a 1–10 fit score
with a recommendation (apply / apply if quick / skip), a per-factor breakdown, and a short
narrative explaining the strengths, risks, and which of my projects to highlight.

**Why this priority**: This is the core value and the engineering differentiator. Without it the
product is just a list. The reproducible hybrid score is what a technical reviewer will scrutinize.

**Independent Test**: With a seeded profile, POST a job payload and assert the response contains a
numeric score in [1,10], a recommendation enum, and a component breakdown whose weighted sum
matches the score. Running the same input twice under the mock provider yields an identical score.

**Acceptance Scenarios**:

1. **Given** a profile with stack [Python, FastAPI, RAG, LangGraph] and a job requiring
   [Python, FastAPI, RAG], **When** the job is scored, **Then** the response returns a score ≥ 7,
   a recommendation of "apply", and a breakdown listing stack_match, seniority_match,
   modality_location, salary_interest, projects_match, and risk_penalty with their weights.
2. **Given** the same profile and the same job payload, **When** scored twice under the mock
   provider, **Then** both responses return the identical numeric score (reproducible).
3. **Given** a job whose stack barely overlaps the profile, **When** scored, **Then** the score is
   low (≤ 4) and the recommendation is "skip", with missing requirements listed in the narrative.
4. **Given** a job missing optional fields (no salary, no location), **When** scored, **Then** the
   system still returns a score, treating the absent factors per documented defaults.

---

### User Story 2 - Track applications on a status board (Priority: P1)

As a job-seeker, after scoring a job I save it as an application and move it through states
(Nueva → Evaluando → Postulado → Seguimiento → Entrevista → Rechazado / Oferta). I can view all
my applications grouped by state, each card showing company, role, score, state, and next action.

**Why this priority**: Tracking is the "CRM" half of the value proposition and makes the product
usable beyond a single scoring call. It is independently demonstrable.

**Independent Test**: Create an application from a scored job, list applications grouped by state,
transition it to a new state, and assert the state change and an event record are persisted.

**Acceptance Scenarios**:

1. **Given** a scored job, **When** I create an application, **Then** it appears on the board in
   the "Nueva" state with its score attached.
2. **Given** an application in "Postulado", **When** I move it to "Entrevista", **Then** the board
   reflects the new state and an application event records actor, timestamp, and transition.
3. **Given** several applications across states, **When** I request the board, **Then** they are
   returned grouped by state in the canonical state order.
4. **Given** an invalid state transition target, **When** I attempt it, **Then** the system
   rejects it with a clear validation error.

---

### User Story 3 - Generate a recruiter outreach message (Priority: P2)

As a job-seeker, for a given application I generate a tailored recruiter message that references
the role and my most relevant projects, in a chosen tone, ready to copy-paste.

**Why this priority**: High-value and "sellable", but depends on having a scored job/application,
so it sequences after P1.

**Independent Test**: For an application, request a generated message and assert a non-empty
message string referencing the role title; under the mock provider the output is deterministic.

**Acceptance Scenarios**:

1. **Given** an application for "Applied AI Engineer", **When** I generate a recruiter message,
   **Then** the response contains a non-empty message that references the role and at least one of
   my highlighted projects.
2. **Given** the same application, **When** I generate a message twice under the mock provider,
   **Then** the outputs are identical (deterministic).
3. **Given** a generated message, **When** it is created, **Then** it is persisted and linked to
   the application for later retrieval.

---

### User Story 4 - Maintain my candidate profile (Priority: P1, foundational)

As a job-seeker, I set up my profile once: skills, projects (with descriptions and tech), seniority,
preferred modality/location, and salary expectation. This profile is the basis for all scoring.

**Why this priority**: Foundational dependency for scoring and messaging; must exist first, even
if seeded.

**Independent Test**: Create/update a profile with skills and projects, read it back, and assert
all fields persisted.

**Acceptance Scenarios**:

1. **Given** no profile, **When** I create one with skills and projects, **Then** it persists and
   is retrievable.
2. **Given** an existing profile, **When** I add a project, **Then** it is available to subsequent
   scoring calls.

---

### Edge Cases

- A job payload with empty/garbage description → system returns a validation error, not a crash.
- A profile with zero skills/projects → scoring still returns a (low) score with a clear note that
  the profile is sparse.
- Extremely long job description → input is bounded/truncated to a documented max length.
- Duplicate job paste → allowed; each creates a distinct opportunity (no dedup required in v1).
- Unauthenticated write request → rejected (Principle V), reads of own data require the token.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST let the single user create and update a candidate profile containing
  skills, projects (title, description, tech), seniority, preferred modality, preferred location,
  and salary expectation.
- **FR-002**: System MUST accept a job opportunity via pasted fields: link, description, company,
  salary (optional), modality, country/location, stack, requirements.
- **FR-003**: System MUST compute a job-fit score from 1 to 10 using a hybrid algorithm composed
  of weighted deterministic components: stack_match (30%), seniority_match (20%),
  modality_location (15%), salary_interest (10%), projects_match (15%), risk_penalty (10%).
- **FR-004**: Stack and project matching MUST use embedding cosine similarity between job
  requirements/stack and the profile's skills/projects (deterministic under the mock embedding
  provider).
- **FR-005**: System MUST NOT derive the numeric score from an LLM. The LLM (mock by default) MAY
  only generate qualitative narrative (risks, missing requirements, projects to highlight,
  rationale) and MUST NOT change the number.
- **FR-006**: System MUST return a recommendation derived deterministically from the score:
  "apply" (≥ 7), "apply if quick" (5–6.9), "skip" (< 5). Thresholds are documented and centralized.
- **FR-007**: System MUST persist each score with its full component breakdown (per-factor
  sub-score and weight) so the recommendation can be explained after the fact.
- **FR-008**: System MUST allow saving a scored job as an Application and MUST track its state
  through the canonical board states: Nueva, Evaluando, Postulado, Seguimiento, Entrevista,
  Rechazado, Oferta.
- **FR-009**: System MUST record an application event (actor, timestamp, from-state, to-state) on
  every state transition and reject transitions to unknown states.
- **FR-010**: System MUST return applications grouped by state in canonical order for the board view.
- **FR-011**: System MUST generate a recruiter outreach message for an application, referencing the
  role and the profile's most relevant projects, and MUST persist it linked to the application.
- **FR-012**: System MUST gate all write operations behind a simple auth token/JWT, even in
  single-user mode, and MUST validate all inputs with schema validation.
- **FR-013**: System MUST emit structured logs for key events: profile_updated, job_created,
  score_computed, message_generated, application_status_changed.
- **FR-014**: System MUST run all tests deterministically with mock providers and MUST make zero
  real LLM/embedding calls in CI.

### Key Entities *(include if feature involves data)*

- **Profile**: The single candidate's identity and preferences (seniority, preferred modality,
  preferred location, salary expectation). Owns Skills and Projects.
- **Skill**: A named competency belonging to the profile (e.g., "FastAPI"), with an embedding
  used for stack matching.
- **Project**: A portfolio project (title, description, tech list) belonging to the profile, with
  an embedding used for projects matching and message highlighting.
- **JobOpportunity**: A pasted job (link, company, description, stack, requirements, modality,
  location, salary), with derived embedding(s) for matching.
- **Score**: The computed fit result for a JobOpportunity vs. the Profile — final number,
  recommendation, and persisted component breakdown plus narrative.
- **Application**: A tracked pursuit of a JobOpportunity, holding current board state and a link to
  its Score and generated messages.
- **ApplicationEvent**: An immutable record of a state transition (actor, timestamp, from→to).
- **GeneratedMessage**: A persisted recruiter message linked to an Application (type, tone, content).
- **Company** *(optional, may be embedded fields on JobOpportunity in v1)*: Company name/metadata.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A user can go from pasting a job to seeing a scored, explained result in a single
  API call (or one screen action) — the demo flow completes in under one minute.
- **SC-002**: Scoring the same profile+job under the mock provider yields a byte-for-byte identical
  numeric score across runs (reproducibility), verified by an automated test.
- **SC-003**: The persisted score breakdown's weighted component sum reconciles to the reported
  final score within rounding tolerance, verified by an automated test.
- **SC-004**: The full test suite passes in CI with mock providers and zero network/LLM calls.
- **SC-005**: 100% of write endpoints reject unauthenticated requests.
- **SC-006**: Every application state transition produces a retrievable event record.

## Assumptions

- Single user (no multi-tenant). Authentication is a simple token/JWT for one account; full user
  management is out of scope for v1.
- Job data is entered manually by pasting fields; no scraping or automated import in v1.
- The frontend (status board) may be a thin Next.js view or deferred; the backend API and tests
  are the primary v1 deliverable and acceptance surface.
- Mock LLM/embedding providers are the default and the only ones used in tests/CI; real providers
  are configurable via environment variables for local/production use.
- The architecture and conventions are reused from the existing AgentDesk AI project
  (providers abstraction, db base mixins, retrieval/cosine logic, conftest patterns, Docker, CI).
- Out of scope for v1: Celery/Redis async jobs, RAG over CV, interview prep, recruiter safety
  check, drag-and-drop Kanban, CSV export, email reminders, calendar/Gmail integration.
