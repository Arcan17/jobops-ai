"""Project — a portfolio project used for matching and message highlighting."""
from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.core.config import settings
from app.db.base import Base, TimestampMixin, UUIDMixin
from app.db.types import Embedding

if TYPE_CHECKING:
    from app.models.profile import Profile


class Project(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "projects"

    profile_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    tech: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    embedding: Mapped[list[float]] = mapped_column(
        Embedding(settings.embedding_dim), nullable=False
    )

    profile: Mapped[Profile] = relationship(back_populates="projects")  # noqa: F821
