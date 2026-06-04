"""Profile — the candidate's identity and preferences; basis for all scoring."""
from __future__ import annotations

import enum
import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Enum as SAEnum
from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.project import Project
    from app.models.skill import Skill


class Seniority(enum.StrEnum):
    junior = "junior"
    mid = "mid"
    senior = "senior"


class Modality(enum.StrEnum):
    remote = "remote"
    hybrid = "hybrid"
    onsite = "onsite"
    any = "any"


class Profile(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "profiles"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True, index=True
    )
    seniority: Mapped[Seniority] = mapped_column(
        SAEnum(Seniority, name="profile_seniority"), nullable=False, default=Seniority.mid
    )
    preferred_modality: Mapped[Modality] = mapped_column(
        SAEnum(Modality, name="profile_modality"), nullable=False, default=Modality.any
    )
    preferred_location: Mapped[str | None] = mapped_column(String(120), nullable=True)
    salary_expectation: Mapped[int | None] = mapped_column(Integer, nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)

    skills: Mapped[list[Skill]] = relationship(  # noqa: F821
        back_populates="profile", cascade="all, delete-orphan", lazy="selectin"
    )
    projects: Mapped[list[Project]] = relationship(  # noqa: F821
        back_populates="profile", cascade="all, delete-orphan", lazy="selectin"
    )
