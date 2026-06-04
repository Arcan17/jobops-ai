"""Recruiter message generation tests."""
from __future__ import annotations

import pytest

from tests.conftest_helpers import STRONG_JOB, create_job, setup_strong_profile


async def _application(client, headers) -> str:
    await setup_strong_profile(client, headers)
    job_id = await create_job(client, headers, STRONG_JOB)
    await client.post(f"/api/v1/jobs/{job_id}/score", headers=headers)
    app = (
        await client.post(
            "/api/v1/applications", headers=headers, json={"job_opportunity_id": job_id}
        )
    ).json()
    return app["id"]


@pytest.mark.asyncio
async def test_generate_message_references_role(client, auth_headers):
    app_id = await _application(client, auth_headers)
    resp = await client.post(
        f"/api/v1/applications/{app_id}/messages",
        headers=auth_headers,
        json={"type": "recruiter_outreach"},
    )
    assert resp.status_code == 201
    content = resp.json()["content"]
    assert content
    assert "Applied AI Engineer" in content


@pytest.mark.asyncio
async def test_message_is_deterministic(client, auth_headers):
    app_id = await _application(client, auth_headers)
    first = (
        await client.post(
            f"/api/v1/applications/{app_id}/messages",
            headers=auth_headers,
            json={"type": "recruiter_outreach"},
        )
    ).json()["content"]
    second = (
        await client.post(
            f"/api/v1/applications/{app_id}/messages",
            headers=auth_headers,
            json={"type": "recruiter_outreach"},
        )
    ).json()["content"]
    assert first == second


@pytest.mark.asyncio
async def test_messages_persisted_and_listable(client, auth_headers):
    app_id = await _application(client, auth_headers)
    await client.post(
        f"/api/v1/applications/{app_id}/messages",
        headers=auth_headers,
        json={"type": "recruiter_outreach"},
    )
    listed = (
        await client.get(f"/api/v1/applications/{app_id}/messages", headers=auth_headers)
    ).json()
    assert len(listed) == 1
    assert listed[0]["type"] == "recruiter_outreach"
