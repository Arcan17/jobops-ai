"""Application — a tracked pursuit of a JobOpportunity, moving through board states."""
from __future__ import annotations

import enum
import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Enum as SAEnum
from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.application_event import ApplicationEvent
    from app.models.generated_message import GeneratedMessage


class ApplicationState(enum.StrEnum):
    nueva = "nueva"
    evaluando = "evaluando"
    postulado = "postulado"
    seguimiento = "seguimiento"
    entrevista = "entrevista"
    rechazado = "rechazado"
    oferta = "oferta"


# Canonical board order (for grouping the board view).
BOARD_ORDER: list[ApplicationState] = [
    ApplicationState.nueva,
    ApplicationState.evaluando,
    ApplicationState.postulado,
    ApplicationState.seguimiento,
    ApplicationState.entrevista,
    ApplicationState.rechazado,
    ApplicationState.oferta,
]

# Allowed state transitions (state machine).
ALLOWED_TRANSITIONS: dict[ApplicationState, set[ApplicationState]] = {
    ApplicationState.nueva: {
        ApplicationState.evaluando,
        ApplicationState.postulado,
        ApplicationState.rechazado,
    },
    ApplicationState.evaluando: {
        ApplicationState.postulado,
        ApplicationState.rechazado,
    },
    ApplicationState.postulado: {
        ApplicationState.seguimiento,
        ApplicationState.entrevista,
        ApplicationState.rechazado,
    },
    ApplicationState.seguimiento: {
        ApplicationState.entrevista,
        ApplicationState.rechazado,
    },
    ApplicationState.entrevista: {
        ApplicationState.oferta,
        ApplicationState.rechazado,
    },
    ApplicationState.rechazado: set(),
    ApplicationState.oferta: set(),
}


class Application(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "applications"

    job_opportunity_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("job_opportunities.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    score_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("scores.id", ondelete="SET NULL"), nullable=True
    )
    state: Mapped[ApplicationState] = mapped_column(
        SAEnum(ApplicationState, name="application_state"),
        nullable=False,
        default=ApplicationState.nueva,
    )
    next_action: Mapped[str | None] = mapped_column(String(300), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    events: Mapped[list[ApplicationEvent]] = relationship(  # noqa: F821
        back_populates="application", cascade="all, delete-orphan", lazy="selectin"
    )
    messages: Mapped[list[GeneratedMessage]] = relationship(  # noqa: F821
        back_populates="application", cascade="all, delete-orphan", lazy="selectin"
    )
