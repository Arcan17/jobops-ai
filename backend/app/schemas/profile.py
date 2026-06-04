"""Profile, Skill, and Project schemas."""
from __future__ import annotations

import uuid

from pydantic import BaseModel, ConfigDict, Field

from app.models.profile import Modality, Seniority


class SkillCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)


class SkillRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    name: str


class ProjectCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str = Field(default="", max_length=5000)
    tech: list[str] = Field(default_factory=list)


class ProjectRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    title: str
    description: str
    tech: list[str]


class ProfileUpdate(BaseModel):
    seniority: Seniority | None = None
    preferred_modality: Modality | None = None
    preferred_location: str | None = Field(default=None, max_length=120)
    salary_expectation: int | None = Field(default=None, ge=0)
    summary: str | None = Field(default=None, max_length=5000)


class ProfileRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    seniority: Seniority
    preferred_modality: Modality
    preferred_location: str | None
    salary_expectation: int | None
    summary: str | None
    skills: list[SkillRead]
    projects: list[ProjectRead]
