"""Recruiter safety analysis — deterministic risk level from detected signals.

The risk level is a pure function of the summed signal severities (no LLM verdict). The output
frames findings as indicators to verify and gives a concrete recommendation, never an accusation.
"""
from __future__ import annotations

from dataclasses import dataclass

from app.core.logging import get_logger
from app.safety.signals import (
    SignalHit,
    detect_structured_signals,
    detect_text_signals,
)

log = get_logger("safety")

# Deterministic thresholds on the summed severity points.
GREEN_MAX = 0
YELLOW_MAX = 2
ORANGE_MAX = 4
# > ORANGE_MAX -> red

_RECOMMENDATION = {
    "green": (
        "No strong risk signals. Still confirm the company and role before sharing documents."
    ),
    "yellow": (
        "Mild signals. Ask for the company name and an official job link before sending your CV."
    ),
    "orange": (
        "Several signals. Request the company, official link, a contract, and a salary range; "
        "verify the recruiter on LinkedIn before proceeding."
    ),
    "red": (
        "High risk. Do not send documents or money. Verify the company independently and "
        "consider reporting the message."
    ),
}


@dataclass(frozen=True)
class SafetyResult:
    risk: str  # green | yellow | orange | red
    score: int  # summed severity points
    signals: list[SignalHit]
    recommendation: str


def _level_for(score: int) -> str:
    if score <= GREEN_MAX:
        return "green"
    if score <= YELLOW_MAX:
        return "yellow"
    if score <= ORANGE_MAX:
        return "orange"
    return "red"


def analyze(
    message: str,
    *,
    email_domain: str | None = None,
    has_official_link: bool | None = None,
    company_named: bool | None = None,
) -> SafetyResult:
    signals = detect_text_signals(message)
    signals += detect_structured_signals(
        email_domain=email_domain,
        has_official_link=has_official_link,
        company_named=company_named,
    )
    score = sum(s.severity for s in signals)
    risk = _level_for(score)
    log.info("safety_checked", risk=risk, score=score, signal_count=len(signals))
    return SafetyResult(
        risk=risk,
        score=score,
        signals=signals,
        recommendation=_RECOMMENDATION[risk],
    )
