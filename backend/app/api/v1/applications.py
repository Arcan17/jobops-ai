"""Applications router: board, state transitions, metadata, and messages."""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.application import (
    ApplicationCreate,
    ApplicationRead,
    ApplicationStateChange,
    ApplicationUpdate,
    BoardResponse,
)
from app.schemas.message import MessageCreate, MessageRead
from app.services import application_service, message_service, profile_service

router = APIRouter(prefix="/applications", tags=["applications"])


@router.post("", response_model=ApplicationRead, status_code=status.HTTP_201_CREATED)
async def create_application(
    data: ApplicationCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApplicationRead:
    profile = await profile_service.get_or_create_profile(db, user.id)
    application = await application_service.create_application(
        db, profile, data.job_opportunity_id
    )
    return ApplicationRead.model_validate(application)


@router.get("/board", response_model=BoardResponse)
async def get_board(
    user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
) -> BoardResponse:
    profile = await profile_service.get_or_create_profile(db, user.id)
    return await application_service.build_board(db, profile)


@router.patch("/{application_id}/state", response_model=ApplicationRead)
async def change_state(
    application_id: uuid.UUID,
    data: ApplicationStateChange,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApplicationRead:
    profile = await profile_service.get_or_create_profile(db, user.id)
    application = await application_service.change_state(
        db, profile, application_id, data.to_state
    )
    return ApplicationRead.model_validate(application)


@router.patch("/{application_id}", response_model=ApplicationRead)
async def update_application(
    application_id: uuid.UUID,
    data: ApplicationUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApplicationRead:
    profile = await profile_service.get_or_create_profile(db, user.id)
    application = await application_service.update_metadata(
        db, profile, application_id, data
    )
    return ApplicationRead.model_validate(application)


@router.post(
    "/{application_id}/messages",
    response_model=MessageRead,
    status_code=status.HTTP_201_CREATED,
)
async def generate_message(
    application_id: uuid.UUID,
    data: MessageCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MessageRead:
    profile = await profile_service.get_or_create_profile(db, user.id)
    application = await application_service.get_application(db, profile, application_id)
    message = await message_service.generate_recruiter_message(
        db, profile, application, message_type=data.type, tone=data.tone
    )
    return MessageRead.model_validate(message)


@router.get("/{application_id}/messages", response_model=list[MessageRead])
async def list_messages(
    application_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[MessageRead]:
    profile = await profile_service.get_or_create_profile(db, user.id)
    application = await application_service.get_application(db, profile, application_id)
    messages = await message_service.list_messages(db, application.id)
    return [MessageRead.model_validate(m) for m in messages]
