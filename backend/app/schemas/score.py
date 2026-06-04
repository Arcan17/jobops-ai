"""Score schemas."""
from __future__ import annotations

import uuid

from pydantic import BaseModel, ConfigDict

from app.models.score import Recommendation


class ScoreComponent(BaseModel):
    factor: str
    weight: float
    sub_score: float  # in [0, 1]
    weighted: float  # weight/100 * sub_score


class ScoreNarrative(BaseModel):
    risks: list[str] = []
    missing_requirements: list[str] = []
    projects_to_highlight: list[str] = []
    rationale: str = ""


class ScoreRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    job_opportunity_id: uuid.UUID
    value: float
    recommendation: Recommendation
    breakdown: list[ScoreComponent]
    narrative: ScoreNarrative
