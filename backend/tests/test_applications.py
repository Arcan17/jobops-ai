"""Application board + state machine tests."""
from __future__ import annotations

import pytest

from tests.conftest_helpers import STRONG_JOB, create_job, setup_strong_profile


async def _scored_job(client, headers) -> str:
    await setup_strong_profile(client, headers)
    job_id = await create_job(client, headers, STRONG_JOB)
    await client.post(f"/api/v1/jobs/{job_id}/score", headers=headers)
    return job_id


@pytest.mark.asyncio
async def test_create_application_starts_in_nueva(client, auth_headers):
    job_id = await _scored_job(client, auth_headers)
    resp = await client.post(
        "/api/v1/applications", headers=auth_headers, json={"job_opportunity_id": job_id}
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["state"] == "nueva"
    assert body["score_id"] is not None


@pytest.mark.asyncio
async def test_board_groups_by_state(client, auth_headers):
    job_id = await _scored_job(client, auth_headers)
    await client.post(
        "/api/v1/applications", headers=auth_headers, json={"job_opportunity_id": job_id}
    )
    board = (await client.get("/api/v1/applications/board", headers=auth_headers)).json()
    states = [col["state"] for col in board["columns"]]
    assert states == [
        "nueva",
        "evaluando",
        "postulado",
        "seguimiento",
        "entrevista",
        "rechazado",
        "oferta",
    ]
    nueva = next(c for c in board["columns"] if c["state"] == "nueva")
    assert len(nueva["cards"]) == 1
    assert nueva["cards"][0]["company"] == "Acme AI"
    assert nueva["cards"][0]["score_value"] is not None


@pytest.mark.asyncio
async def test_valid_transition_records_event(client, auth_headers):
    job_id = await _scored_job(client, auth_headers)
    app = (
        await client.post(
            "/api/v1/applications", headers=auth_headers, json={"job_opportunity_id": job_id}
        )
    ).json()
    resp = await client.patch(
        f"/api/v1/applications/{app['id']}/state",
        headers=auth_headers,
        json={"to_state": "postulado"},
    )
    assert resp.status_code == 200
    assert resp.json()["state"] == "postulado"


@pytest.mark.asyncio
async def test_invalid_transition_rejected(client, auth_headers):
    job_id = await _scored_job(client, auth_headers)
    app = (
        await client.post(
            "/api/v1/applications", headers=auth_headers, json={"job_opportunity_id": job_id}
        )
    ).json()
    # nueva -> oferta is not allowed
    resp = await client.patch(
        f"/api/v1/applications/{app['id']}/state",
        headers=auth_headers,
        json={"to_state": "oferta"},
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_duplicate_application_conflict(client, auth_headers):
    job_id = await _scored_job(client, auth_headers)
    await client.post(
        "/api/v1/applications", headers=auth_headers, json={"job_opportunity_id": job_id}
    )
    dup = await client.post(
        "/api/v1/applications", headers=auth_headers, json={"job_opportunity_id": job_id}
    )
    assert dup.status_code == 409
