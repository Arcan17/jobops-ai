"""Embedding similarity helpers used by the scoring engine.

Cosine similarity between a job's embedding and the profile's skill/project embeddings.
Pure in-Python cosine keeps the computation deterministic and dialect-independent; the
embeddings themselves come from the (mock by default) embedding provider. The pgvector
``<=>`` operator is used for any future ranked DB retrieval, but per-pair scoring here is
in Python because both operands are already loaded.
"""
from __future__ import annotations

import math

from app.providers.factory import get_embedding_provider


def cosine(a: list[float], b: list[float]) -> float:
    # Coerce to native floats: pgvector returns numpy float32, which is not JSON
    # serializable once it propagates into the persisted score breakdown.
    af = [float(x) for x in a]
    bf = [float(y) for y in b]
    dot = sum(x * y for x, y in zip(af, bf, strict=False))
    na = math.sqrt(sum(x * x for x in af))
    nb = math.sqrt(sum(y * y for y in bf))
    if na == 0.0 or nb == 0.0:
        return 0.0
    return float(dot / (na * nb))


def normalize_similarity(value: float) -> float:
    """Map cosine [-1, 1] into [0, 1]."""
    return float(max(0.0, min(1.0, (value + 1.0) / 2.0)))


async def embed_text(text: str) -> list[float]:
    return (await get_embedding_provider().embed([text]))[0]


def mean_top_k(target: list[float], candidates: list[list[float]], k: int) -> float:
    """Mean of the top-k normalized cosine similarities; 0.0 if no candidates."""
    if not candidates:
        return 0.0
    sims = sorted(
        (normalize_similarity(cosine(target, c)) for c in candidates), reverse=True
    )
    top = sims[: max(1, k)]
    return sum(top) / len(top)


def max_similarity(target: list[float], candidates: list[list[float]]) -> float:
    if not candidates:
        return 0.0
    return max(normalize_similarity(cosine(target, c)) for c in candidates)
