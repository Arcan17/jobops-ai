# ADR 0002 — LLM/embedding provider abstraction with mock default

**Status**: Accepted · 2026-06-04

## Context

The system needs embeddings (for matching) and LLM text (for narrative/messages). Calling a vendor
SDK directly would create lock-in, cost, flaky tests, and network dependency in CI.

## Decision

All LLM/embedding access goes through abstract interfaces (`LLMProvider`, `EmbeddingProvider`) in
`app/providers/`. Concrete adapters (Anthropic, OpenAI, Mock) are selected by environment variable
via a cached factory. The deterministic `MockProvider` is the default and the ONLY provider used in
tests and CI. Vendor SDKs are imported lazily and only inside their adapter modules.

The mock embedding provider hashes bag-of-words into an L2-normalized vector, so equal text yields
equal vectors and shared vocabulary yields higher cosine similarity — enough to exercise the real
matching/scoring code paths deterministically.

## Consequences

- CI is free, fast, and never flaky; no API keys required.
- Scores and generated messages are reproducible.
- Swapping to a real provider is an env-var change; no business code changes.
