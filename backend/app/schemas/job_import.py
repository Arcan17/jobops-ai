"""Schemas for importing jobs from public JOB_HUNT sources."""
from __future__ import annotations

from pydantic import BaseModel, Field

from app.schemas.job import JobRead
from app.schemas.score import ScoreRead


class RankedImportedJob(BaseModel):
    job: JobRead
    score: ScoreRead


class JobImportSourceResult(BaseModel):
    source: str
    fetched: int
    created: int
    skipped_duplicates: int
    jobs: list[JobRead]
    ranked: list[RankedImportedJob] = Field(default_factory=list)


class JobImportResponse(BaseModel):
    fetched: int
    created: int
    skipped_duplicates: int
    sources: list[JobImportSourceResult]
    ranked: list[RankedImportedJob] = []
    shortlist: list[RankedImportedJob] = Field(default_factory=list)
