"""GeneratedMessage schemas."""
from __future__ import annotations

import uuid

from pydantic import BaseModel, ConfigDict, Field

from app.models.generated_message import MessageType


class MessageCreate(BaseModel):
    type: MessageType = MessageType.recruiter_outreach
    tone: str | None = Field(default=None, max_length=60)


class MessageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    application_id: uuid.UUID
    type: MessageType
    tone: str | None
    content: str
