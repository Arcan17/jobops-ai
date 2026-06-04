# Phase 1 Data Model: JobOps AI — MVP

All tables use `UUIDMixin` (uuid PK) and `TimestampMixin` (`created_at`, `updated_at`,
tz-aware, server defaults) from `app/db/base.py`. Single-user → no `organization_id`.

## Entities

### User
The single seeded account used for JWT auth.
- `email` (unique), `hashed_password`, `is_active`.
- Relationship: 1–1 `Profile` (in practice one user, one profile).

### Profile
Candidate identity & preferences; basis for all scoring.
- `user_id` (FK → User), `seniority` (enum: junior/mid/senior), `preferred_modality`
  (enum: remote/hybrid/onsite/any), `preferred_location` (str, nullable),
  `salary_expectation` (int, nullable, currency-agnostic), `summary` (text, nullable).
- Relationships: many `Skill`, many `Project`.

### Skill
A named competency on the profile.
- `profile_id` (FK), `name` (str), `embedding` (Embedding vector).
- Embedding computed on create/update via `EmbeddingProvider`.

### Project
A portfolio project used for matching and message highlighting.
- `profile_id` (FK), `title` (str), `description` (text), `tech` (str[] / JSON),
  `embedding` (Embedding vector over title+description+tech).

### JobOpportunity
A pasted job (structured input).
- `profile_id` (FK), `link` (str, nullable), `company` (str), `role_title` (str),
  `description` (text), `stack` (str[] / JSON), `requirements` (text),
  `modality` (enum: remote/hybrid/onsite/unknown), `country` (str, nullable),
  `salary` (int, nullable), `embedding` (Embedding over stack+requirements).
- Relationship: 0–1 `Score` (latest), 0–1 `Application`.

### Score
Computed fit result for a JobOpportunity vs. Profile.
- `job_opportunity_id` (FK, unique per latest compute), `value` (float 1–10),
  `recommendation` (enum: apply/apply_if_quick/skip),
  `breakdown` (JSON: list of {factor, weight, sub_score, weighted}),
  `narrative` (JSON/text: {risks[], missing_requirements[], projects_to_highlight[], rationale}).
- Invariant: `value` == round(sum(weighted), 1) within tolerance; weights sum to 100.

### Application
A tracked pursuit of a JobOpportunity.
- `job_opportunity_id` (FK), `score_id` (FK, nullable), `state` (enum, see below),
  `next_action` (str, nullable), `notes` (text, nullable), `applied_at` (datetime, nullable).
- Relationships: many `ApplicationEvent`, many `GeneratedMessage`.

### ApplicationEvent
Immutable state-transition record.
- `application_id` (FK), `actor` (str), `from_state` (enum, nullable),
  `to_state` (enum), `created_at`.

### GeneratedMessage
A persisted recruiter outreach message.
- `application_id` (FK), `type` (enum: recruiter_outreach — only v1),
  `tone` (str, nullable), `content` (text).

## Enums

**ApplicationState** (canonical order):
`nueva → evaluando → postulado → seguimiento → entrevista → rechazado | oferta`

Allowed transitions (state machine):
- nueva → evaluando, postulado, rechazado
- evaluando → postulado, rechazado
- postulado → seguimiento, entrevista, rechazado
- seguimiento → entrevista, rechazado
- entrevista → oferta, rechazado
- rechazado → (terminal)
- oferta → (terminal)

**Recommendation**: apply (score ≥ 7), apply_if_quick (5 ≤ score < 7), skip (score < 5).

## Relationship Summary

```
User 1──1 Profile 1──* Skill
                  1──* Project
                  1──* JobOpportunity 1──1 Score
                                      1──1 Application 1──* ApplicationEvent
                                                       1──* GeneratedMessage
```

## Scoring Components (deterministic)

| Factor | Weight | Computation |
|---|---|---|
| stack_match | 30 | mean top-k cosine(job.stack+requirements, profile.skills) → [0,1] |
| seniority_match | 20 | rule: exact=1.0, ±1 level=0.6, else 0.2 |
| modality_location | 15 | rule: modality match + location/remote compatibility |
| projects_match | 15 | max/mean cosine(job, profile.projects) → [0,1] |
| salary_interest | 10 | rule: salary ≥ expectation=1.0, within 20%=0.7, unknown=0.5, below=0.3 |
| risk_penalty | 10 | rule: starts at 1.0, subtract per detected blocker (e.g., language/onsite) |

Final: `value = 1 + 9 * Σ(weight_i/100 * sub_score_i)` → mapped into [1,10], rounded to 1 decimal.
Breakdown persists each factor's `weight`, `sub_score`, and `weighted = weight/100 * sub_score`.
