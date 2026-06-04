"""GeneratedMessage — a persisted recruiter outreach message linked to an Application."""
from __future__ import annotations

import enum
import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Enum as SAEnum
from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.application import Application


class MessageType(enum.StrEnum):
    recruiter_outreach = "recruiter_outreach"


class GeneratedMessage(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "generated_messages"

    application_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("applications.id", ondelete="CASCADE"), nullable=False, index=True
    )
    type: Mapped[MessageType] = mapped_column(
        SAEnum(MessageType, name="message_type"),
        nullable=False,
        default=MessageType.recruiter_outreach,
    )
    tone: Mapped[str | None] = mapped_column(String(60), nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)

    application: Mapped[Application] = relationship(back_populates="messages")  # noqa: F821
