"""Deterministic, offline mock providers.

Embeddings are reproducible (hashed bag-of-words -> L2-normalized vector) so equal text
yields equal vectors and texts sharing words yield higher cosine similarity. Completions
are templated and grounded in the prompt/context. No network, no cost.
"""
from __future__ import annotations

import hashlib
import math
import re

from app.providers.base import EmbeddingProvider, LLMProvider, LLMResult

_WORD_RE = re.compile(r"[a-z0-9]+")


def _tokens(text: str) -> list[str]:
    return _WORD_RE.findall(text.lower())


class MockEmbeddingProvider(EmbeddingProvider):
    name = "mock"

    def __init__(self, dim: int = 384) -> None:
        self.dim = dim

    def _embed_one(self, text: str) -> list[float]:
        vec = [0.0] * self.dim
        for tok in _tokens(text):
            h = int.from_bytes(hashlib.sha256(tok.encode()).digest()[:8], "big")
            idx = h % self.dim
            sign = 1.0 if (h >> 8) & 1 else -1.0
            vec[idx] += sign
        norm = math.sqrt(sum(v * v for v in vec))
        if norm == 0.0:
            # empty/unknown text -> stable non-zero unit vector
            vec[0] = 1.0
            return vec
        return [v / norm for v in vec]

    async def embed(self, texts: list[str]) -> list[list[float]]:
        return [self._embed_one(t) for t in texts]


class MockLLMProvider(LLMProvider):
    name = "mock"

    async def complete(
        self, prompt: str, *, system: str | None = None, **opts: object
    ) -> LLMResult:
        # Deterministic recruiter-style message grounded in the structured context.
        role = str(opts.get("role", "the role")).strip() or "the role"
        company = str(opts.get("company", "your team")).strip() or "your team"
        raw_projects = opts.get("projects")
        projects: list[str] = []
        if isinstance(raw_projects, str):
            projects = [raw_projects]
        elif isinstance(raw_projects, (list, tuple)):
            projects = [str(p) for p in raw_projects]
        projects_clause = ""
        if projects:
            joined = ", ".join(projects)
            projects_clause = f" My most relevant work includes {joined}."
        body = (
            f"Hi, thanks for reaching out about the {role} role at {company}. "
            f"I'm very interested and believe my background is a strong fit.{projects_clause} "
            "I'd be glad to share more or set up a quick call."
        )
        prompt_tokens = len(_tokens(prompt)) + (len(_tokens(system)) if system else 0)
        completion_tokens = len(_tokens(body))
        return LLMResult(
            text=body,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            model="mock-1",
        )
