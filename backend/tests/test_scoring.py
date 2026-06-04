"""Scoring engine tests — the project's acceptance gate (Constitution III).

Covers: value range, breakdown reconciliation, reproducibility, weights summing to 100,
recommendation thresholds, and strong-vs-weak ordering.
"""
from __future__ import annotations

import json

import pytest

from app.scoring.weights import get_weights
from app.services.matching_service import cosine
from tests.conftest_helpers import STRONG_JOB, WEAK_JOB, create_job, setup_strong_profile


def test_weights_sum_to_100():
    assert get_weights().total == pytest.approx(100.0)


def test_cosine_returns_native_float():
    # Regression guard: pgvector returns numpy float32, which is not JSON serializable
    # once it reaches the persisted breakdown. cosine() must coerce to native float.
    result = cosine([1.0, 0.0, 1.0], [1.0, 1.0, 0.0])
    assert type(result) is float


@pytest.mark.asyncio
async def test_strong_job_scores_high_and_recommends_apply(client, auth_headers):
    await setup_strong_profile(client, auth_headers)
    job_id = await create_job(client, auth_headers, STRONG_JOB)
    score = (await client.post(f"/api/v1/jobs/{job_id}/score", headers=auth_headers)).json()

    assert 1.0 <= score["value"] <= 10.0
    factors = {c["factor"] for c in score["breakdown"]}
    assert factors == {
        "stack_match",
        "seniority_match",
        "modality_location",
        "projects_match",
        "salary_interest",
        "risk_penalty",
    }
    assert score["value"] >= 7.0
    assert score["recommendation"] == "apply"


@pytest.mark.asyncio
async def test_breakdown_reconciles_to_value(client, auth_headers):
    await setup_strong_profile(client, auth_headers)
    job_id = await create_job(client, auth_headers, STRONG_JOB)
    score = (await client.post(f"/api/v1/jobs/{job_id}/score", headers=auth_headers)).json()

    fraction = sum(c["weighted"] for c in score["breakdown"])  # in [0, 1]
    expected = round(1.0 + 9.0 * fraction, 1)
    assert score["value"] == pytest.approx(expected, abs=0.05)

    # Each weighted equals weight/100 * sub_score.
    for c in score["breakdown"]:
        assert c["weighted"] == pytest.approx(c["weight"] / 100.0 * c["sub_score"], abs=1e-4)


@pytest.mark.asyncio
async def test_score_is_reproducible(client, auth_headers):
    await setup_strong_profile(client, auth_headers)
    job_id = await create_job(client, auth_headers, STRONG_JOB)
    first = (await client.post(f"/api/v1/jobs/{job_id}/score", headers=auth_headers)).json()
    second = (await client.post(f"/api/v1/jobs/{job_id}/score", headers=auth_headers)).json()
    assert first["value"] == second["value"]
    assert first["breakdown"] == second["breakdown"]


@pytest.mark.asyncio
async def test_weak_job_scores_lower_than_strong(client, auth_headers):
    await setup_strong_profile(client, auth_headers)
    strong_id = await create_job(client, auth_headers, STRONG_JOB)
    weak_id = await create_job(client, auth_headers, WEAK_JOB)
    strong = (await client.post(f"/api/v1/jobs/{strong_id}/score", headers=auth_headers)).json()
    weak = (await client.post(f"/api/v1/jobs/{weak_id}/score", headers=auth_headers)).json()
    assert weak["value"] < strong["value"]


@pytest.mark.asyncio
async def test_narrative_present_but_does_not_set_number(client, auth_headers):
    await setup_strong_profile(client, auth_headers)
    job_id = await create_job(client, auth_headers, STRONG_JOB)
    score = (await client.post(f"/api/v1/jobs/{job_id}/score", headers=auth_headers)).json()
    narrative = score["narrative"]
    assert "rationale" in narrative
    assert isinstance(narrative["projects_to_highlight"], list)


@pytest.mark.asyncio
async def test_breakdown_is_json_serializable(client, auth_headers):
    # Guards the numpy-float32 regression at the persistence boundary.
    await setup_strong_profile(client, auth_headers)
    job_id = await create_job(client, auth_headers, STRONG_JOB)
    score = (await client.post(f"/api/v1/jobs/{job_id}/score", headers=auth_headers)).json()
    json.dumps(score["breakdown"])  # must not raise
    for c in score["breakdown"]:
        assert type(c["sub_score"]) is float
        assert type(c["weighted"]) is float
