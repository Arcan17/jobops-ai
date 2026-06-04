"""Profile CRUD tests."""
from __future__ import annotations

import pytest


@pytest.mark.asyncio
async def test_get_creates_empty_profile(client, auth_headers):
    resp = await client.get("/api/v1/profile", headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["skills"] == []
    assert body["projects"] == []


@pytest.mark.asyncio
async def test_update_profile(client, auth_headers):
    resp = await client.put(
        "/api/v1/profile",
        headers=auth_headers,
        json={"seniority": "senior", "preferred_modality": "remote", "salary_expectation": 5000},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["seniority"] == "senior"
    assert body["preferred_modality"] == "remote"
    assert body["salary_expectation"] == 5000


@pytest.mark.asyncio
async def test_add_skill_and_project(client, auth_headers):
    s = await client.post(
        "/api/v1/profile/skills", headers=auth_headers, json={"name": "FastAPI"}
    )
    assert s.status_code == 201
    p = await client.post(
        "/api/v1/profile/projects",
        headers=auth_headers,
        json={"title": "AgentDesk AI", "description": "RAG support bot", "tech": ["FastAPI"]},
    )
    assert p.status_code == 201

    profile = (await client.get("/api/v1/profile", headers=auth_headers)).json()
    assert {s["name"] for s in profile["skills"]} == {"FastAPI"}
    assert profile["projects"][0]["title"] == "AgentDesk AI"


@pytest.mark.asyncio
async def test_delete_skill(client, auth_headers):
    s = await client.post(
        "/api/v1/profile/skills", headers=auth_headers, json={"name": "Redis"}
    )
    skill_id = s.json()["id"]
    d = await client.delete(f"/api/v1/profile/skills/{skill_id}", headers=auth_headers)
    assert d.status_code == 204
    profile = (await client.get("/api/v1/profile", headers=auth_headers)).json()
    assert profile["skills"] == []
