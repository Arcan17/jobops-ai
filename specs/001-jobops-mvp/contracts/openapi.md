# Phase 1 API Contracts: JobOps AI — MVP

All endpoints under `/api/v1`. Writes require `Authorization: Bearer <jwt>`. Inputs/outputs are
Pydantic v2 schemas. This is a summary; the live OpenAPI is served at `/docs`.

## Auth
- `POST /auth/login` — body `{email, password}` → `{access_token, token_type}`. Validates against
  the seeded user.

## Health
- `GET /health` → `{status: "ok"}` (no auth).

## Profile
- `GET /profile` → current profile with skills & projects.
- `PUT /profile` — body `{seniority, preferred_modality, preferred_location, salary_expectation, summary}` → updated profile.
- `POST /profile/skills` — body `{name}` → created skill (embedding computed).
- `DELETE /profile/skills/{id}` → 204.
- `POST /profile/projects` — body `{title, description, tech[]}` → created project (embedding computed).
- `DELETE /profile/projects/{id}` → 204.

## Jobs
- `POST /jobs` — body `{link?, company, role_title, description, stack[], requirements, modality, country?, salary?}`
  → created JobOpportunity.
- `GET /jobs` → list of jobs.
- `GET /jobs/{id}` → job detail (+ latest score if computed).
- `POST /jobs/{id}/score` → computes & persists Score:
  `{value, recommendation, breakdown:[{factor, weight, sub_score, weighted}], narrative:{risks[], missing_requirements[], projects_to_highlight[], rationale}}`.
  Deterministic under mock provider.

## Applications (board)
- `POST /applications` — body `{job_opportunity_id}` → creates Application in state `nueva`
  (attaches latest score).
- `GET /applications/board` → applications grouped by state in canonical order; each card:
  `{id, company, role_title, score_value, state, next_action}`.
- `PATCH /applications/{id}/state` — body `{to_state}` → validates transition, records
  ApplicationEvent, returns updated application. Invalid transition → 422.
- `PATCH /applications/{id}` — body `{next_action?, notes?}` → update card metadata.

## Messages
- `POST /applications/{id}/messages` — body `{type:"recruiter_outreach", tone?}` → generated
  message referencing role + top projects; persisted & returned. Deterministic under mock.
- `GET /applications/{id}/messages` → list of generated messages for the application.

## Error model
- Validation errors → 422 with field detail (FastAPI/Pydantic default).
- Auth failures → 401. Unknown resource → 404. No stack traces/secrets leaked.
