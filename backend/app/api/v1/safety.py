"""Recruiter safety check router (stateless analysis)."""
from __future__ import annotations

from fastapi import APIRouter, Depends

from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.safety import SafetyCheckRequest, SafetyCheckResponse, SignalRead
from app.services import safety_service

router = APIRouter(prefix="/safety", tags=["safety"])


@router.post("/check", response_model=SafetyCheckResponse)
async def check_recruiter(
    data: SafetyCheckRequest,
    _user: User = Depends(get_current_user),
) -> SafetyCheckResponse:
    result = safety_service.analyze(
        data.message,
        email_domain=data.email_domain,
        has_official_link=data.has_official_link,
        company_named=data.company_named,
    )
    return SafetyCheckResponse(
        risk=result.risk,
        score=result.score,
        signals=[SignalRead(**s.__dict__) for s in result.signals],
        recommendation=result.recommendation,
    )
