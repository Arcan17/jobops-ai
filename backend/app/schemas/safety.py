"""Recruiter safety check schemas."""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class SafetyCheckRequest(BaseModel):
    message: str = Field(min_length=1, max_length=20000)
    email_domain: str | None = Field(default=None, max_length=255)
    has_official_link: bool | None = None
    company_named: bool | None = None


class SignalRead(BaseModel):
    code: str
    label: str
    severity: int
    detail: str


class SafetyCheckResponse(BaseModel):
    risk: Literal["green", "yellow", "orange", "red"]
    score: int
    signals: list[SignalRead]
    recommendation: str
