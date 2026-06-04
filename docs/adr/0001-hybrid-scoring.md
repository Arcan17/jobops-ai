# ADR 0001 — Hybrid scoring (deterministic number + LLM narrative)

**Status**: Accepted · 2026-06-04

## Context

Job-fit needs a 1–10 score with a recommendation. A naive approach asks an LLM to return a number.
That is non-deterministic, untestable, and unconvincing to a technical reviewer. The score is the
product's differentiator and must be explainable and reproducible.

## Decision

Compute the number deterministically as a weighted sum of per-factor sub-scores:
`stack_match (30)`, `seniority_match (20)`, `modality_location (15)`, `projects_match (15)`,
`salary_interest (10)`, `risk_penalty (10)`. Stack/project matching uses embedding cosine
similarity; the rest are rules. The LLM (mock by default) only writes the narrative (risks,
missing requirements, projects to highlight, rationale) and **never** affects the number.

Weights and thresholds live in `app/scoring/weights.py` (overridable via settings). Each score
persists its full component breakdown.

## Consequences

- The score is reproducible under the mock provider and asserted by `tests/test_scoring.py`
  (reproducibility + breakdown reconciliation + weights summing to 100).
- Tuning is centralized and transparent.
- Adding a factor means adding a deterministic component function and a weight — the LLM path is
  untouched.
