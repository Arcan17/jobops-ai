# Phase 0 Research: JobOps AI — MVP

## Decisions & Rationale

### D1. Hybrid scoring (deterministic number + LLM narrative)
**Decision**: The 1–10 score is a weighted sum of deterministic per-factor sub-scores. The LLM
(mock by default) only writes the narrative (risks, missing requirements, projects to highlight).
**Rationale**: Reproducibility and explainability are the project's differentiator (Constitution
III). An LLM-produced number is non-deterministic, untestable, and unimpressive to reviewers.
**Alternatives rejected**: Pure-LLM scoring (non-deterministic, not testable); pure keyword
matching (brittle, ignores semantic similarity).

### D2. Embedding-based stack/project matching with dual-dialect retrieval
**Decision**: Compute embeddings for skills, projects, and job stack/requirements; score stack and
project match by cosine similarity. Use pgvector `<=>` on PostgreSQL and an in-Python cosine
fallback on SQLite (tests). Reuse AgentDesk's `retrieval_service.py` logic.
**Rationale**: Semantic match beats exact-string match; the dual-dialect approach keeps CI on
SQLite with no extension while production uses pgvector. Already proven in AgentDesk.
**Alternatives rejected**: External vector DB (Chroma/Pinecone) — extra infra, single-DB is simpler.

### D3. Deterministic mock providers as default
**Decision**: `MockEmbeddingProvider` (hash-based, L2-normalized, reproducible) and
`MockLLMProvider` (templated) are the default and the only providers in tests/CI.
**Rationale**: Constitution II & IV — free, fast, non-flaky CI; reproducible scores.

### D4. Scoring weights centralized & configurable
**Decision**: Weights live in `app/scoring/weights.py` (and overridable via settings): stack 30,
seniority 20, modality_location 15, projects 15, salary_interest 10, risk_penalty 10.
Recommendation thresholds centralized too: apply ≥ 7, apply-if-quick 5–6.9, skip < 5.
**Rationale**: Explainability and easy tuning; tests assert weights sum to 100 and breakdown
reconciles to the final score.

### D5. Single-user JWT auth with seeded user
**Decision**: JWT issued at login for one seeded user (provisioned via env/seed script). No
registration / RBAC / multi-tenant.
**Rationale**: Demonstrates real auth (Constitution V) without SaaS scope creep. Reuses AgentDesk
`security.py`.
**Alternatives rejected**: Static API token (less credible); full registration (out of MVP scope).

### D6. Structured job input (no LLM parsing)
**Decision**: Jobs are entered as structured fields, validated by Pydantic v2.
**Rationale**: Keeps the score path deterministic; LLM text-extraction would reintroduce
non-determinism into the critical flow. Optional autofill-from-text is a v2 idea outside the score
path.

### D7. Frontend optional in v1
**Decision**: Backend API + tests are the acceptance surface; a thin Next.js board is optional.
**Rationale**: The defensible scoring engine and tests are what reviewers scrutinize; a board can
be a follow-up without blocking v1 value.

## Open Questions
None blocking. All Session 2026-06-04 clarifications resolved in spec.md.
