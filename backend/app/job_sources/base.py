"""Normalized external job representation used by JOB_HUNT sources."""
from __future__ import annotations

from dataclasses import dataclass

from app.models.job_opportunity import Modality
from app.schemas.job import JobCreate


@dataclass(frozen=True, slots=True)
class ExternalJob:
    source: str
    external_id: str
    link: str
    company: str
    role_title: str
    description: str = ""
    stack: tuple[str, ...] = ()
    requirements: str = ""
    modality: Modality = Modality.unknown
    country: str | None = None
    salary: int | None = None

    def to_job_create(self) -> JobCreate:
        return JobCreate(
            link=self.link,
            company=self.company,
            role_title=self.role_title,
            description=self.description[:20000],
            stack=list(self.stack),
            requirements=self.requirements[:20000],
            modality=self.modality,
            country=self.country,
            salary=self.salary,
        )
