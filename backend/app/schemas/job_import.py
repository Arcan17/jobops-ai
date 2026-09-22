"""Schemas for importing jobs from public JOB_HUNT sources."""
from __future__ import annotations

from pydantic import BaseModel

from app.schemas.job import JobRead


class JobImportSourceResult(BaseModel):
    source: str
    fetched: int
    created: int
    skipped_duplicates: int
    jobs: list[JobRead]


class JobImportResponse(BaseModel):
    fetched: int
    created: int
    skipped_duplicates: int
    sources: list[JobImportSourceResult]
