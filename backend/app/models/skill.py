"""Skill — a named competency on the profile, with an embedding for stack matching."""
from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.config import settings
from app.db.base import Base, TimestampMixin, UUIDMixin
from app.db.types import Embedding

if TYPE_CHECKING:
    from app.models.profile import Profile


class Skill(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "skills"

    profile_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    embedding: Mapped[list[float]] = mapped_column(
        Embedding(settings.embedding_dim), nullable=False
    )

    profile: Mapped[Profile] = relationship(back_populates="skills")  # noqa: F821
