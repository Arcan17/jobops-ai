"""Profile, skill, and project business logic.

Embeddings for skills and projects are computed on create via the embedding provider
(mock by default) so they are immediately available to the scoring engine.
"""
from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.models.profile import Profile
from app.models.project import Project
from app.models.skill import Skill
from app.providers.factory import get_embedding_provider
from app.schemas.profile import ProfileUpdate, ProjectCreate, SkillCreate

log = get_logger("profile")


async def get_or_create_profile(db: AsyncSession, user_id: uuid.UUID) -> Profile:
    profile = await db.scalar(select(Profile).where(Profile.user_id == user_id))
    if profile is None:
        profile = Profile(user_id=user_id)
        db.add(profile)
        await db.commit()
        await db.refresh(profile)
    return profile


async def update_profile(
    db: AsyncSession, profile: Profile, data: ProfileUpdate
) -> Profile:
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(profile, field, value)
    await db.commit()
    await db.refresh(profile)
    log.info("profile_updated", profile_id=str(profile.id))
    return profile


async def add_skill(db: AsyncSession, profile: Profile, data: SkillCreate) -> Skill:
    embedding = (await get_embedding_provider().embed([data.name]))[0]
    skill = Skill(profile_id=profile.id, name=data.name, embedding=embedding)
    db.add(skill)
    await db.commit()
    await db.refresh(skill)
    return skill


async def delete_skill(db: AsyncSession, profile: Profile, skill_id: uuid.UUID) -> bool:
    skill = await db.get(Skill, skill_id)
    if skill is None or skill.profile_id != profile.id:
        return False
    await db.delete(skill)
    await db.commit()
    db.expire(profile)  # reload the skills collection on next access
    return True


async def add_project(db: AsyncSession, profile: Profile, data: ProjectCreate) -> Project:
    text = f"{data.title}\n{data.description}\n{' '.join(data.tech)}"
    embedding = (await get_embedding_provider().embed([text]))[0]
    project = Project(
        profile_id=profile.id,
        title=data.title,
        description=data.description,
        tech=data.tech,
        embedding=embedding,
    )
    db.add(project)
    await db.commit()
    await db.refresh(project)
    return project


async def delete_project(
    db: AsyncSession, profile: Profile, project_id: uuid.UUID
) -> bool:
    project = await db.get(Project, project_id)
    if project is None or project.profile_id != profile.id:
        return False
    await db.delete(project)
    await db.commit()
    db.expire(profile)  # reload the projects collection on next access
    return True
