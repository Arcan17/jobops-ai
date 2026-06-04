"""Recruiter outreach message generation (the only message type in v1).

Builds a prompt from the role and the profile's top-matching projects, then delegates to
the LLM provider (mock by default → deterministic output). Persists the message linked to
the application.
"""
from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.models.application import Application
from app.models.generated_message import GeneratedMessage, MessageType
from app.models.job_opportunity import JobOpportunity
from app.models.profile import Profile
from app.providers.factory import get_llm_provider
from app.services import matching_service as M

log = get_logger("messages")


def _top_projects(profile: Profile, job: JobOpportunity, k: int = 3) -> list[str]:
    ranked = sorted(
        profile.projects,
        key=lambda p: M.normalize_similarity(M.cosine(job.embedding, p.embedding)),
        reverse=True,
    )
    return [p.title for p in ranked[:k]]


async def generate_recruiter_message(
    db: AsyncSession,
    profile: Profile,
    application: Application,
    *,
    message_type: MessageType = MessageType.recruiter_outreach,
    tone: str | None = None,
) -> GeneratedMessage:
    job = await db.get(JobOpportunity, application.job_opportunity_id)
    assert job is not None  # ownership already verified by caller
    projects = _top_projects(profile, job)

    llm = get_llm_provider()
    prompt = (
        f"Write a short outreach message to a recruiter for the {job.role_title} role "
        f"at {job.company}."
    )
    result = await llm.complete(
        prompt,
        system="You write concise, professional recruiter outreach messages.",
        role=job.role_title,
        company=job.company,
        projects=projects,
        tone=tone or "professional",
    )
    message = GeneratedMessage(
        application_id=application.id,
        type=message_type,
        tone=tone,
        content=result.text,
    )
    db.add(message)
    await db.commit()
    await db.refresh(message)
    log.info("message_generated", application_id=str(application.id), type=message_type.value)
    return message


async def list_messages(
    db: AsyncSession, application_id: uuid.UUID
) -> list[GeneratedMessage]:
    application = await db.get(Application, application_id)
    if application is None:
        return []
    return list(application.messages)
