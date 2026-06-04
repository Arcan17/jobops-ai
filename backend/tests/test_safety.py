"""Recruiter safety check tests — deterministic risk levels."""
from __future__ import annotations

import pytest

from app.services.safety_service import analyze


def test_clean_message_is_green():
    result = analyze(
        "Hi Bastian, I'm a recruiter at Acme Corp hiring a Backend Engineer. "
        "Here is the official posting on our careers site. Happy to chat.",
        email_domain="acme.com",
        has_official_link=True,
        company_named=True,
    )
    assert result.risk == "green"
    assert result.score == 0
    assert result.signals == []


def test_free_email_and_no_link_is_orange():
    result = analyze(
        "Hello, we have an opening at our firm.",
        email_domain="gmail.com",
        has_official_link=False,
        company_named=True,
    )
    # free_email (2) + no_official_link (2) = 4 -> orange.
    assert result.risk == "orange"
    assert result.score == 4
    codes = {s.code for s in result.signals}
    assert "free_email_domain" in codes
    assert "no_official_link" in codes


def test_payment_request_is_red():
    result = analyze(
        "Congratulations! You are hired immediately, no interview needed. "
        "Please pay a small registration fee and message me on WhatsApp.",
        email_domain="gmail.com",
        has_official_link=False,
        company_named=False,
    )
    assert result.risk == "red"
    codes = {s.code for s in result.signals}
    assert "upfront_payment" in codes
    assert "unofficial_channel" in codes


def test_documents_request_detected():
    result = analyze("Please send a photo of your passport and bank account to proceed.")
    codes = {s.code for s in result.signals}
    assert "personal_documents" in codes


def test_is_deterministic():
    msg = "Urgent! Dear candidate, send your CV and pay a deposit."
    a = analyze(msg, email_domain="hotmail.com")
    b = analyze(msg, email_domain="hotmail.com")
    assert a.risk == b.risk
    assert a.score == b.score
    assert [s.code for s in a.signals] == [s.code for s in b.signals]


@pytest.mark.asyncio
async def test_safety_endpoint_requires_auth(client):
    resp = await client.post("/api/v1/safety/check", json={"message": "hi"})
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_safety_endpoint_returns_risk(client, auth_headers):
    resp = await client.post(
        "/api/v1/safety/check",
        headers=auth_headers,
        json={
            "message": "Pay a registration fee and contact me on Telegram.",
            "email_domain": "gmail.com",
            "has_official_link": False,
            "company_named": False,
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["risk"] == "red"
    assert body["score"] >= 5
    assert any(s["code"] == "upfront_payment" for s in body["signals"])
    assert body["recommendation"]
