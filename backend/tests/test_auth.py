"""Auth + write-protection tests."""
from __future__ import annotations

import pytest


@pytest.mark.asyncio
async def test_login_returns_jwt(client, user):
    resp = await client.post(
        "/api/v1/auth/login", json={"email": "me@example.com", "password": "secret123"}
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["access_token"]
    assert body["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_wrong_password(client, user):
    resp = await client.post(
        "/api/v1/auth/login", json={"email": "me@example.com", "password": "wrong"}
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_writes_require_token(client):
    resp = await client.post("/api/v1/profile/skills", json={"name": "Python"})
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_health_is_public(client):
    resp = await client.get("/api/v1/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"
