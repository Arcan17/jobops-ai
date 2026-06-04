"""Profile router: profile, skills, projects."""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.profile import (
    ProfileRead,
    ProfileUpdate,
    ProjectCreate,
    ProjectRead,
    SkillCreate,
    SkillRead,
)
from app.services import profile_service

router = APIRouter(prefix="/profile", tags=["profile"])


@router.get("", response_model=ProfileRead)
async def read_profile(
    user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
) -> ProfileRead:
    profile = await profile_service.get_or_create_profile(db, user.id)
    return ProfileRead.model_validate(profile)


@router.put("", response_model=ProfileRead)
async def update_profile(
    data: ProfileUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ProfileRead:
    profile = await profile_service.get_or_create_profile(db, user.id)
    profile = await profile_service.update_profile(db, profile, data)
    return ProfileRead.model_validate(profile)


@router.post("/skills", response_model=SkillRead, status_code=status.HTTP_201_CREATED)
async def add_skill(
    data: SkillCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SkillRead:
    profile = await profile_service.get_or_create_profile(db, user.id)
    skill = await profile_service.add_skill(db, profile, data)
    return SkillRead.model_validate(skill)


@router.delete("/skills/{skill_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_skill(
    skill_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    profile = await profile_service.get_or_create_profile(db, user.id)
    ok = await profile_service.delete_skill(db, profile, skill_id)
    if not ok:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Skill not found")


@router.post("/projects", response_model=ProjectRead, status_code=status.HTTP_201_CREATED)
async def add_project(
    data: ProjectCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ProjectRead:
    profile = await profile_service.get_or_create_profile(db, user.id)
    project = await profile_service.add_project(db, profile, data)
    return ProjectRead.model_validate(project)


@router.delete("/projects/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    profile = await profile_service.get_or_create_profile(db, user.id)
    ok = await profile_service.delete_project(db, profile, project_id)
    if not ok:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Project not found")
