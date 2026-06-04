"""JobOpportunity — a pasted job (structured input) scored against the profile."""
from __future__ import annotations

import enum
import uuid

from sqlalchemy import Enum as SAEnum
from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON

from app.core.config import settings
from app.db.base import Base, TimestampMixin, UUIDMixin
from app.db.types import Embedding


class Modality(enum.StrEnum):
    remote = "remote"
    hybrid = "hybrid"
    onsite = "onsite"
    unknown = "unknown"


class JobOpportunity(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "job_opportunities"

    profile_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    link: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    company: Mapped[str] = mapped_column(String(200), nullable=False)
    role_title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    stack: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    requirements: Mapped[str] = mapped_column(Text, nullable=False, default="")
    modality: Mapped[Modality] = mapped_column(
        SAEnum(Modality, name="job_modality"), nullable=False, default=Modality.unknown
    )
    country: Mapped[str | None] = mapped_column(String(120), nullable=True)
    salary: Mapped[int | None] = mapped_column(Integer, nullable=True)
    embedding: Mapped[list[float]] = mapped_column(
        Embedding(settings.embedding_dim), nullable=False
    )
