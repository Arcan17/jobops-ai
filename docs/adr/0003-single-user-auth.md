# ADR 0003 — Single-user JWT auth (no multi-tenant in v1)

**Status**: Accepted · 2026-06-04

## Context

JobOps AI v1 is a personal tool for one candidate. Full multi-tenant SaaS (organizations, RBAC,
registration) would add significant scope without v1 value, while leaving writes unauthenticated
would model poor security posture.

## Decision

Use JWT auth bound to a single seeded user (provisioned via `app/seed.py` from env credentials).
`POST /auth/login` issues an access token; all write endpoints require it. No self-service
registration, roles, or `organization_id` scoping in v1.

## Consequences

- Demonstrates real authentication and input validation without SaaS scope creep.
- The data model has no tenant columns; introducing multi-tenancy later is a deliberate v3 step
  (add `organization_id`, scope queries, add registration) rather than an accidental leak.
- Tests authenticate by minting a token for a seeded user (`tests/conftest.py`).
