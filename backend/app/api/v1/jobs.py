"""Jobs router: create/list/get jobs and compute the hybrid score."""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.job import JobCreate, JobRead
from app.schemas.job_import import JobImportResponse
from app.schemas.score import ScoreRead
from app.services import job_import_service, job_service, profile_service, scoring_service
from app.services.job_import_service import JobSource

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.post("", response_model=JobRead, status_code=status.HTTP_201_CREATED)
async def create_job(
    data: JobCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> JobRead:
    profile = await profile_service.get_or_create_profile(db, user.id)
    job = await job_service.create_job(db, profile, data)
    return JobRead.model_validate(job)


@router.get("", response_model=list[JobRead])
async def list_jobs(
    user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
) -> list[JobRead]:
    profile = await profile_service.get_or_create_profile(db, user.id)
    jobs = await job_service.list_jobs(db, profile)
    return [JobRead.model_validate(j) for j in jobs]


@router.post("/import", response_model=JobImportResponse)
async def import_public_jobs(
    sources: list[JobSource] | None = Query(default=None),
    limit_per_source: int = Query(default=25, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> JobImportResponse:
    """Import and deduplicate jobs from approved public feeds."""
    profile = await profile_service.get_or_create_profile(db, user.id)
    selected_sources = sources or [JobSource.remoteok, JobSource.wwr]
    return await job_import_service.import_jobs(
        db,
        profile,
        selected_sources,
        limit_per_source=limit_per_source,
    )


@router.get("/{job_id}", response_model=JobRead)
async def get_job(
    job_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> JobRead:
    profile = await profile_service.get_or_create_profile(db, user.id)
    job = await job_service.get_job(db, profile, job_id)
    if job is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Job not found")
    return JobRead.model_validate(job)


@router.post("/{job_id}/score", response_model=ScoreRead)
async def score_job(
    job_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ScoreRead:
    profile = await profile_service.get_or_create_profile(db, user.id)
    job = await job_service.get_job(db, profile, job_id)
    if job is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Job not found")
    score = await scoring_service.score_job(db, profile, job)
    return ScoreRead.model_validate(score)
