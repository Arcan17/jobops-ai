"""Application and board schemas."""
from __future__ import annotations

import uuid

from pydantic import BaseModel, ConfigDict, Field

from app.models.application import ApplicationState


class ApplicationCreate(BaseModel):
    job_opportunity_id: uuid.UUID


class ApplicationStateChange(BaseModel):
    to_state: ApplicationState


class ApplicationUpdate(BaseModel):
    next_action: str | None = Field(default=None, max_length=300)
    notes: str | None = Field(default=None, max_length=5000)


class ApplicationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    job_opportunity_id: uuid.UUID
    score_id: uuid.UUID | None
    state: ApplicationState
    next_action: str | None
    notes: str | None


class BoardCard(BaseModel):
    id: uuid.UUID
    company: str
    role_title: str
    score_value: float | None
    state: ApplicationState
    next_action: str | None


class BoardColumn(BaseModel):
    state: ApplicationState
    cards: list[BoardCard]


class BoardResponse(BaseModel):
    columns: list[BoardColumn]
