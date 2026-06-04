"""Deterministic per-factor sub-score functions.

Each returns a sub-score in [0, 1]. These are pure functions of structured inputs and
precomputed similarities — no LLM, no randomness — so the overall score is reproducible
(Constitution III). The risk factor returns a *retention* value in [0,1] (1.0 = no risk),
applied with its weight like any other positive factor.
"""
from __future__ import annotations

from app.models.job_opportunity import JobOpportunity
from app.models.job_opportunity import Modality as JobModality
from app.models.profile import Modality as ProfileModality
from app.models.profile import Profile, Seniority

_SENIORITY_ORDER = {Seniority.junior: 0, Seniority.mid: 1, Seniority.senior: 2}

# Tokens in requirements/description that indicate a potential blocker.
_RISK_TOKENS = {
    "english": "advanced English may be required",
    "fluent": "fluency expectations",
    "clearance": "security clearance",
    "onsite": "on-site presence",
    "on-site": "on-site presence",
    "relocation": "relocation",
}


def clamp01(x: float) -> float:
    return max(0.0, min(1.0, x))


def stack_match(similarity: float) -> float:
    """Sub-score from mean top-k cosine similarity (already in [0,1]-ish)."""
    return clamp01(similarity)


def projects_match(similarity: float) -> float:
    return clamp01(similarity)


def seniority_match(profile: Profile, job_text: str) -> float:
    """Infer the job's seniority from its text; compare to the profile level.

    Exact = 1.0, one level away = 0.6, otherwise 0.2. If the job gives no signal,
    return a neutral 0.7 (we don't penalize missing data hard).
    """
    text = job_text.lower()
    inferred: Seniority | None = None
    if "senior" in text or "sr." in text or "lead" in text:
        inferred = Seniority.senior
    elif "junior" in text or "jr." in text or "entry" in text:
        inferred = Seniority.junior
    elif "mid" in text or "intermediate" in text:
        inferred = Seniority.mid
    if inferred is None:
        return 0.7
    distance = abs(_SENIORITY_ORDER[inferred] - _SENIORITY_ORDER[profile.seniority])
    return {0: 1.0, 1: 0.6}.get(distance, 0.2)


def modality_location(profile: Profile, job: JobOpportunity) -> float:
    """Compatibility of job modality/location with the profile preference."""
    pref = profile.preferred_modality
    job_mod = job.modality

    if pref == ProfileModality.any:
        modality_score = 1.0
    elif job_mod == JobModality.unknown:
        modality_score = 0.6
    elif pref.value == job_mod.value:
        modality_score = 1.0
    elif pref == ProfileModality.remote and job_mod == JobModality.hybrid:
        modality_score = 0.6
    elif pref == ProfileModality.hybrid and job_mod in (JobModality.remote, JobModality.onsite):
        modality_score = 0.7
    else:
        modality_score = 0.3

    # Remote roles make location irrelevant; otherwise reward a location match.
    if job_mod == JobModality.remote or pref in (ProfileModality.remote, ProfileModality.any):
        location_score = 1.0
    elif profile.preferred_location and job.country:
        location_score = 1.0 if profile.preferred_location.lower() in job.country.lower() else 0.4
    else:
        location_score = 0.6

    return clamp01(0.6 * modality_score + 0.4 * location_score)


def salary_interest(profile: Profile, job: JobOpportunity) -> float:
    """Reward salary meeting expectation; neutral when unknown."""
    expectation = profile.salary_expectation
    salary = job.salary
    if salary is None or expectation is None or expectation == 0:
        return 0.5  # unknown -> neutral
    if salary >= expectation:
        return 1.0
    ratio = salary / expectation
    if ratio >= 0.8:
        return 0.7
    return 0.3


def risk_penalty(job: JobOpportunity) -> tuple[float, list[str]]:
    """Detect blockers from job text; return (retention in [0,1], risk notes).

    Each detected blocker subtracts 0.25 from a starting 1.0 retention value.
    """
    text = f"{job.requirements}\n{job.description}".lower()
    notes: list[str] = []
    seen: set[str] = set()
    for token, label in _RISK_TOKENS.items():
        if token in text and label not in seen:
            notes.append(label)
            seen.add(label)
    retention = clamp01(1.0 - 0.25 * len(notes))
    return retention, notes
