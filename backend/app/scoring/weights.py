"""Centralized scoring weights and recommendation thresholds.

Weights MUST sum to 100. They are sourced from settings (overridable via env) so the
scoring is tunable in one place and assertable in tests (Constitution III).
"""
from __future__ import annotations

from dataclasses import dataclass

from app.core.config import settings
from app.models.score import Recommendation

# Factor keys — the single source of truth for breakdown factor names.
STACK = "stack_match"
SENIORITY = "seniority_match"
MODALITY_LOCATION = "modality_location"
PROJECTS = "projects_match"
SALARY = "salary_interest"
RISK = "risk_penalty"


@dataclass(frozen=True)
class Weights:
    stack: float
    seniority: float
    modality_location: float
    projects: float
    salary: float
    risk: float

    def as_dict(self) -> dict[str, float]:
        return {
            STACK: self.stack,
            SENIORITY: self.seniority,
            MODALITY_LOCATION: self.modality_location,
            PROJECTS: self.projects,
            SALARY: self.salary,
            RISK: self.risk,
        }

    @property
    def total(self) -> float:
        return (
            self.stack
            + self.seniority
            + self.modality_location
            + self.projects
            + self.salary
            + self.risk
        )


def get_weights() -> Weights:
    return Weights(
        stack=settings.weight_stack,
        seniority=settings.weight_seniority,
        modality_location=settings.weight_modality_location,
        projects=settings.weight_projects,
        salary=settings.weight_salary,
        risk=settings.weight_risk,
    )


def recommendation_for(value: float) -> Recommendation:
    """Deterministic mapping from the 1-10 score to a recommendation."""
    if value >= settings.recommend_apply_min:
        return Recommendation.apply
    if value >= settings.recommend_quick_min:
        return Recommendation.apply_if_quick
    return Recommendation.skip
