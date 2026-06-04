"""Score — the computed fit result for a JobOpportunity vs. the Profile.

Persists the full component breakdown (Constitution VI: Explainability), not just the
final number, so any recommendation can be explained after the fact.
"""
from __future__ import annotations

import enum
import uuid

from sqlalchemy import Enum as SAEnum
from sqlalchemy import Float, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON

from app.db.base import Base, TimestampMixin, UUIDMixin


class Recommendation(enum.StrEnum):
    apply = "apply"
    apply_if_quick = "apply_if_quick"
    skip = "skip"


class Score(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "scores"

    job_opportunity_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("job_opportunities.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    value: Mapped[float] = mapped_column(Float, nullable=False)
    recommendation: Mapped[Recommendation] = mapped_column(
        SAEnum(Recommendation, name="score_recommendation"), nullable=False
    )
    # breakdown: list[{factor, weight, sub_score, weighted}]
    breakdown: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    # narrative: {risks[], missing_requirements[], projects_to_highlight[], rationale}
    narrative: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
