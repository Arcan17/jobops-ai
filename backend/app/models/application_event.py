"""ApplicationEvent — an immutable record of a state transition."""
from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Enum as SAEnum
from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDMixin
from app.models.application import ApplicationState

if TYPE_CHECKING:
    from app.models.application import Application


class ApplicationEvent(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "application_events"

    application_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("applications.id", ondelete="CASCADE"), nullable=False, index=True
    )
    actor: Mapped[str] = mapped_column(String(120), nullable=False)
    from_state: Mapped[ApplicationState | None] = mapped_column(
        SAEnum(ApplicationState, name="application_state", create_type=False), nullable=True
    )
    to_state: Mapped[ApplicationState] = mapped_column(
        SAEnum(ApplicationState, name="application_state", create_type=False), nullable=False
    )

    application: Mapped[Application] = relationship(back_populates="events")  # noqa: F821
