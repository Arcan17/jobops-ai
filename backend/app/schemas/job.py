"""JobOpportunity schemas (structured input — no LLM parsing)."""
from __future__ import annotations

import uuid

from pydantic import BaseModel, ConfigDict, Field

from app.models.job_opportunity import Modality


class JobCreate(BaseModel):
    link: str | None = Field(default=None, max_length=1000)
    company: str = Field(min_length=1, max_length=200)
    role_title: str = Field(min_length=1, max_length=200)
    description: str = Field(default="", max_length=20000)
    stack: list[str] = Field(default_factory=list)
    requirements: str = Field(default="", max_length=20000)
    modality: Modality = Modality.unknown
    country: str | None = Field(default=None, max_length=120)
    salary: int | None = Field(default=None, ge=0)


class JobRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    link: str | None
    company: str
    role_title: str
    description: str
    stack: list[str]
    requirements: str
    modality: Modality
    country: str | None
    salary: int | None
