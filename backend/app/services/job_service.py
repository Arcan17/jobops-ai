"""JobOpportunity business logic."""
from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.models.job_opportunity import JobOpportunity
from app.models.profile import Profile
from app.providers.factory import get_embedding_provider
from app.schemas.job import JobCreate

log = get_logger("jobs")


def job_embedding_text(data: JobCreate) -> str:
    return f"{data.role_title}\n{' '.join(data.stack)}\n{data.requirements}\n{data.description}"


async def create_job(
    db: AsyncSession, profile: Profile, data: JobCreate
) -> JobOpportunity:
    embedding = (await get_embedding_provider().embed([job_embedding_text(data)]))[0]
    job = JobOpportunity(
        profile_id=profile.id,
        link=data.link,
        company=data.company,
        role_title=data.role_title,
        description=data.description,
        stack=data.stack,
        requirements=data.requirements,
        modality=data.modality,
        country=data.country,
        salary=data.salary,
        embedding=embedding,
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)
    log.info("job_created", job_id=str(job.id), company=job.company)
    return job


async def list_jobs(db: AsyncSession, profile: Profile) -> list[JobOpportunity]:
    return list(
        await db.scalars(
            select(JobOpportunity)
            .where(JobOpportunity.profile_id == profile.id)
            .order_by(JobOpportunity.created_at.desc())
        )
    )


async def get_job(
    db: AsyncSession, profile: Profile, job_id: uuid.UUID
) -> JobOpportunity | None:
    job = await db.get(JobOpportunity, job_id)
    if job is None or job.profile_id != profile.id:
        return None
    return job
