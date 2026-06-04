"""Deterministic recruiter-message risk signals.

Each signal is detected by an explicit rule (keywords + a few structured flags) and carries a
severity weight. The overall risk level is a deterministic function of the summed weights — never
an LLM verdict. Signals are framed as *indicators to verify*, not accusations (Constitution III:
defensible, deterministic; this mirrors the scoring philosophy for risk).
"""
from __future__ import annotations

import re
from dataclasses import dataclass

# Free/personal email providers — a corporate role normally writes from a company domain.
FREE_EMAIL_DOMAINS = {
    "gmail.com",
    "hotmail.com",
    "outlook.com",
    "yahoo.com",
    "proton.me",
    "protonmail.com",
    "icloud.com",
    "live.com",
    "aol.com",
}


@dataclass(frozen=True)
class SignalHit:
    code: str
    label: str
    severity: int  # weight points
    detail: str


@dataclass(frozen=True)
class _Rule:
    code: str
    label: str
    severity: int
    patterns: tuple[str, ...]
    detail: str


# Keyword rules over the message text. Patterns are lowercase substrings / simple regex.
_TEXT_RULES: tuple[_Rule, ...] = (
    _Rule(
        "unofficial_channel",
        "Asks to move to WhatsApp/Telegram",
        2,
        ("whatsapp", "telegram", "signal app", "move to chat", "text me on"),
        "Legitimate recruiters usually keep first contact on email/LinkedIn.",
    ),
    _Rule(
        "personal_documents",
        "Requests personal documents",
        3,
        (
            "passport",
            "national id",
            "driver's license",
            "ssn",
            "social security",
            "dni",
            "bank account",
        ),
        "Identity/financial documents are not needed to start a conversation.",
    ),
    _Rule(
        "upfront_payment",
        "Mentions an upfront payment or fee",
        4,
        ("registration fee", "training fee", "pay for", "deposit", "processing fee", "send money"),
        "You should never pay to be hired. Strong scam indicator.",
    ),
    _Rule(
        "no_interview",
        "Offers the job with no interview / guaranteed hire",
        2,
        ("no interview", "guaranteed", "immediate hire", "hired immediately", "start today"),
        "Real hiring involves an evaluation step.",
    ),
    _Rule(
        "urgency_pressure",
        "Creates urgency / pressure",
        1,
        ("urgent", "act now", "limited slots", "asap", "respond within", "expires"),
        "Pressure tactics discourage due diligence.",
    ),
    _Rule(
        "generic_greeting",
        "Generic, templated greeting",
        1,
        ("dear candidate", "dear applicant", "hello dear", "dear sir/madam"),
        "Impersonal greeting suggests mass outreach.",
    ),
    _Rule(
        "asks_cv",
        "Asks for your CV/resume early",
        1,
        ("send your cv", "send your resume", "share your cv", "attach your resume"),
        "Fine on its own, but verify the company first if combined with other signals.",
    ),
)


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower())


def detect_text_signals(message: str) -> list[SignalHit]:
    norm = _normalize(message)
    hits: list[SignalHit] = []
    for rule in _TEXT_RULES:
        if any(p in norm for p in rule.patterns):
            hits.append(SignalHit(rule.code, rule.label, rule.severity, rule.detail))
    return hits


def detect_structured_signals(
    *,
    email_domain: str | None,
    has_official_link: bool | None,
    company_named: bool | None,
) -> list[SignalHit]:
    hits: list[SignalHit] = []
    if email_domain and email_domain.lower().strip() in FREE_EMAIL_DOMAINS:
        hits.append(
            SignalHit(
                "free_email_domain",
                "Writes from a free email domain",
                2,
                f"'{email_domain}' is a personal provider, not a corporate domain.",
            )
        )
    if has_official_link is False:
        hits.append(
            SignalHit(
                "no_official_link",
                "No official company link provided",
                2,
                "Ask for the company website / official job posting.",
            )
        )
    if company_named is False:
        hits.append(
            SignalHit(
                "no_company_named",
                "Does not name the hiring company",
                2,
                "A real recruiter names the company they represent.",
            )
        )
    return hits
