"""Hybrid job-fit scoring engine (the project's centerpiece).

The numeric score is a weighted sum of deterministic per-factor sub-scores
(Constitution III). The LLM (mock by default) is used ONLY to phrase the narrative and
MUST NOT change the number. Given the same profile + job under the mock providers, the
score is reproducible.
"""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.logging import get_logger
from app.models.job_opportunity import JobOpportunity
from app.models.profile import Profile
from app.models.score import Score
from app.providers.factory import get_llm_provider
from app.scoring import components as C
from app.scoring import weights as W
from app.services import matching_service as M

log = get_logger("scoring")


def _round(x: float) -> float:
    return float(round(float(x), 4))


async def compute_components(
    db: AsyncSession, profile: Profile, job: JobOpportunity
) -> tuple[list[dict], list[str], list[str]]:
    """Return (breakdown, risk_notes, missing_requirements).

    breakdown items: {factor, weight, sub_score, weighted}.
    """
    weights = W.get_weights()
    skill_embeddings = [s.embedding for s in profile.skills]
    project_embeddings = [p.embedding for p in profile.projects]

    stack_sim = M.mean_top_k(job.embedding, skill_embeddings, settings.match_top_k)
    projects_sim = M.max_similarity(job.embedding, project_embeddings)

    job_text = f"{job.role_title} {job.requirements} {job.description}"
    retention, risk_notes = C.risk_penalty(job)

    subscores = {
        W.STACK: C.stack_match(stack_sim),
        W.SENIORITY: C.seniority_match(profile, job_text),
        W.MODALITY_LOCATION: C.modality_location(profile, job),
        W.PROJECTS: C.projects_match(projects_sim),
        W.SALARY: C.salary_interest(profile, job),
        W.RISK: retention,
    }
    weight_map = weights.as_dict()
    breakdown = [
        {
            "factor": factor,
            "weight": weight_map[factor],
            "sub_score": _round(subscores[factor]),
            "weighted": _round(weight_map[factor] / 100.0 * subscores[factor]),
        }
        for factor in weight_map
    ]

    # Missing requirements: profile skills with weak stack coverage signal gaps.
    missing: list[str] = []
    if stack_sim < 0.5:
        missing.append("Some required stack items have weak overlap with your skills")
    if not profile.skills:
        missing.append("No skills on profile to match against")

    return breakdown, risk_notes, missing


def aggregate(breakdown: list[dict]) -> float:
    """Map the sum of weighted sub-scores (0..1) onto the 1-10 scale, 1 decimal."""
    fraction = sum(item["weighted"] for item in breakdown)  # in [0, 1]
    value = 1.0 + 9.0 * fraction
    return round(value, 1)


async def _narrative(
    profile: Profile,
    job: JobOpportunity,
    value: float,
    risk_notes: list[str],
    missing: list[str],
) -> dict:
    # Deterministically pick the top projects to highlight (by similarity to the job).
    ranked = sorted(
        profile.projects,
        key=lambda p: M.normalize_similarity(M.cosine(job.embedding, p.embedding)),
        reverse=True,
    )
    projects_to_highlight = [p.title for p in ranked[:3]]

    # LLM is used only for the prose rationale; it never affects the number.
    llm = get_llm_provider()
    prompt = (
        f"Explain in one sentence why a candidate scored {value}/10 for the role "
        f"{job.role_title} at {job.company}."
    )
    result = await llm.complete(
        prompt,
        system="You summarize job fit briefly.",
        role=job.role_title,
        company=job.company,
        projects=projects_to_highlight,
    )
    return {
        "risks": risk_notes,
        "missing_requirements": missing,
        "projects_to_highlight": projects_to_highlight,
        "rationale": result.text,
    }


async def score_job(db: AsyncSession, profile: Profile, job: JobOpportunity) -> Score:
    breakdown, risk_notes, missing = await compute_components(db, profile, job)
    value = aggregate(breakdown)
    recommendation = W.recommendation_for(value)
    narrative = await _narrative(profile, job, value, risk_notes, missing)

    existing = await db.scalar(
        select(Score).where(Score.job_opportunity_id == job.id)
    )
    if existing is None:
        score = Score(
            job_opportunity_id=job.id,
            value=value,
            recommendation=recommendation,
            breakdown=breakdown,
            narrative=narrative,
        )
        db.add(score)
    else:
        existing.value = value
        existing.recommendation = recommendation
        existing.breakdown = breakdown
        existing.narrative = narrative
        score = existing
    await db.commit()
    await db.refresh(score)
    log.info(
        "score_computed",
        job_id=str(job.id),
        value=value,
        recommendation=recommendation.value,
    )
    return score
