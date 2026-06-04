"""Seed the single user (and an optional sample profile) for local/demo use.

Run with: ``python -m app.seed``. Credentials come from settings (env).
Idempotent: re-running does not duplicate the user.
"""
from __future__ import annotations

import asyncio

from sqlalchemy import select

from app.core.config import settings
from app.core.logging import get_logger
from app.core.security import hash_password
from app.db.engine import SessionLocal
from app.models.user import User
from app.schemas.profile import ProjectCreate, SkillCreate
from app.services import profile_service

log = get_logger("seed")

SAMPLE_SKILLS = ["Python", "FastAPI", "RAG", "LangGraph", "PostgreSQL", "Docker"]
SAMPLE_PROJECTS = [
    ProjectCreate(
        title="AgentDesk AI",
        description="Human-in-the-loop AI SupportOps platform with LangGraph and RAG.",
        tech=["FastAPI", "LangGraph", "pgvector", "Celery"],
    ),
    ProjectCreate(
        title="PrivRAG",
        description="Privacy-preserving RAG pipeline with PII scrubbing and caching.",
        tech=["Python", "RAG", "pgvector"],
    ),
]


async def seed() -> None:
    async with SessionLocal() as db:
        user = await db.scalar(select(User).where(User.email == settings.seed_user_email))
        if user is None:
            user = User(
                email=settings.seed_user_email,
                hashed_password=hash_password(settings.seed_user_password),
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)
            log.info("seed_user_created", email=user.email)
        else:
            log.info("seed_user_exists", email=user.email)

        profile = await profile_service.get_or_create_profile(db, user.id)
        if not profile.skills:
            for name in SAMPLE_SKILLS:
                await profile_service.add_skill(db, profile, SkillCreate(name=name))
            for project in SAMPLE_PROJECTS:
                await profile_service.add_project(db, profile, project)
            log.info("seed_profile_populated", profile_id=str(profile.id))


if __name__ == "__main__":
    asyncio.run(seed())
