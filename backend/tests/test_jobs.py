"""Job creation/listing tests."""
from __future__ import annotations

import pytest

from tests.conftest_helpers import STRONG_JOB, create_job


@pytest.mark.asyncio
async def test_create_and_get_job(client, auth_headers):
    job_id = await create_job(client, auth_headers, STRONG_JOB)
    resp = await client.get(f"/api/v1/jobs/{job_id}", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["company"] == "Acme AI"


@pytest.mark.asyncio
async def test_list_jobs(client, auth_headers):
    await create_job(client, auth_headers, STRONG_JOB)
    resp = await client.get("/api/v1/jobs", headers=auth_headers)
    assert resp.status_code == 200
    assert len(resp.json()) == 1


@pytest.mark.asyncio
async def test_create_job_validation_error(client, auth_headers):
    resp = await client.post(
        "/api/v1/jobs", headers=auth_headers, json={"role_title": "x"}  # missing company
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_get_unknown_job_404(client, auth_headers):
    resp = await client.get(
        "/api/v1/jobs/00000000-0000-0000-0000-000000000000", headers=auth_headers
    )
    assert resp.status_code == 404
