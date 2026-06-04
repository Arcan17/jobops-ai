"""Application board business logic: create, state machine, board grouping."""
from __future__ import annotations

import uuid

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.models.application import (
    ALLOWED_TRANSITIONS,
    BOARD_ORDER,
    Application,
    ApplicationState,
)
from app.models.application_event import ApplicationEvent
from app.models.job_opportunity import JobOpportunity
from app.models.profile import Profile
from app.models.score import Score
from app.schemas.application import (
    ApplicationUpdate,
    BoardCard,
    BoardColumn,
    BoardResponse,
)

log = get_logger("applications")


async def create_application(
    db: AsyncSession, profile: Profile, job_id: uuid.UUID
) -> Application:
    job = await db.get(JobOpportunity, job_id)
    if job is None or job.profile_id != profile.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Job opportunity not found")

    existing = await db.scalar(
        select(Application).where(Application.job_opportunity_id == job_id)
    )
    if existing is not None:
        raise HTTPException(
            status.HTTP_409_CONFLICT, "Application already exists for this job"
        )

    score = await db.scalar(select(Score).where(Score.job_opportunity_id == job_id))
    application = Application(
        job_opportunity_id=job_id,
        score_id=score.id if score else None,
        state=ApplicationState.nueva,
    )
    db.add(application)
    await db.flush()
    db.add(
        ApplicationEvent(
            application_id=application.id,
            actor="user",
            from_state=None,
            to_state=ApplicationState.nueva,
        )
    )
    await db.commit()
    await db.refresh(application)
    return application


async def _get_owned(
    db: AsyncSession, profile: Profile, application_id: uuid.UUID
) -> Application:
    application = await db.get(Application, application_id)
    if application is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Application not found")
    job = await db.get(JobOpportunity, application.job_opportunity_id)
    if job is None or job.profile_id != profile.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Application not found")
    return application


async def change_state(
    db: AsyncSession,
    profile: Profile,
    application_id: uuid.UUID,
    to_state: ApplicationState,
) -> Application:
    application = await _get_owned(db, profile, application_id)
    current = application.state
    if to_state not in ALLOWED_TRANSITIONS.get(current, set()):
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            f"Invalid transition: {current.value} -> {to_state.value}",
        )
    application.state = to_state
    db.add(
        ApplicationEvent(
            application_id=application.id,
            actor="user",
            from_state=current,
            to_state=to_state,
        )
    )
    await db.commit()
    await db.refresh(application)
    log.info(
        "application_status_changed",
        application_id=str(application.id),
        from_state=current.value,
        to_state=to_state.value,
    )
    return application


async def update_metadata(
    db: AsyncSession,
    profile: Profile,
    application_id: uuid.UUID,
    data: ApplicationUpdate,
) -> Application:
    application = await _get_owned(db, profile, application_id)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(application, field, value)
    await db.commit()
    await db.refresh(application)
    return application


async def get_application(
    db: AsyncSession, profile: Profile, application_id: uuid.UUID
) -> Application:
    return await _get_owned(db, profile, application_id)


async def build_board(db: AsyncSession, profile: Profile) -> BoardResponse:
    rows = await db.execute(
        select(Application, JobOpportunity, Score)
        .join(JobOpportunity, Application.job_opportunity_id == JobOpportunity.id)
        .join(Score, Application.score_id == Score.id, isouter=True)
        .where(JobOpportunity.profile_id == profile.id)
    )
    cards_by_state: dict[ApplicationState, list[BoardCard]] = {s: [] for s in BOARD_ORDER}
    for application, job, score in rows.all():
        cards_by_state[application.state].append(
            BoardCard(
                id=application.id,
                company=job.company,
                role_title=job.role_title,
                score_value=score.value if score else None,
                state=application.state,
                next_action=application.next_action,
            )
        )
    columns = [
        BoardColumn(state=state, cards=cards_by_state[state]) for state in BOARD_ORDER
    ]
    return BoardResponse(columns=columns)
