"""JOB_HUNT V1 source parsing and import tests (fully offline)."""
from __future__ import annotations

from app.job_sources.base import ExternalJob
from app.job_sources.remoteok import parse_remoteok_payload
from app.job_sources.wwr import parse_wwr_rss
from app.models.job_opportunity import Modality
from app.services import job_import_service


def test_remoteok_parser_skips_metadata_and_normalizes_job() -> None:
    jobs = parse_remoteok_payload(
        [
            {"legal": "metadata row"},
            {
                "id": "123",
                "company": "Example",
                "position": "Python Backend Developer",
                "description": "FastAPI and PostgreSQL",
                "tags": ["python", "fastapi"],
                "location": "Worldwide",
                "url": "https://remoteok.com/remote-jobs/123",
            },
        ]
    )
    assert len(jobs) == 1
    assert jobs[0].company == "Example"
    assert jobs[0].role_title == "Python Backend Developer"
    assert jobs[0].stack == ("python", "fastapi")
    assert jobs[0].modality == Modality.remote


def test_wwr_parser_normalizes_rss() -> None:
    payload = """<?xml version="1.0"?>
    <rss><channel>
      <item>
        <title>Acme: Backend Engineer</title>
        <link>https://weworkremotely.com/remote-jobs/acme-backend</link>
        <guid>wwr-1</guid>
        <description><![CDATA[<p>Python, FastAPI and PostgreSQL.</p>]]></description>
        <category>Back-End Programming</category>
      </item>
    </channel></rss>
    """
    jobs = parse_wwr_rss(payload)
    assert len(jobs) == 1
    assert jobs[0].company == "Acme"
    assert jobs[0].role_title == "Backend Engineer"
    assert jobs[0].description == "Python, FastAPI and PostgreSQL."
    assert jobs[0].modality == Modality.remote


async def test_import_endpoint_deduplicates_existing_links(
    client,
    auth_headers,
    monkeypatch,
) -> None:
    async def fake_remoteok(limit: int):
        assert limit == 10
        return [
            ExternalJob(
                source="remoteok",
                external_id="job-1",
                link="https://example.test/jobs/1",
                company="Example",
                role_title="Backend Developer",
                description="Python FastAPI",
                stack=("python", "fastapi"),
                modality=Modality.remote,
            )
        ]

    monkeypatch.setitem(
        job_import_service.FETCHERS,
        job_import_service.JobSource.remoteok,
        fake_remoteok,
    )

    first = await client.post(
        "/api/v1/jobs/import?sources=remoteok&limit_per_source=10",
        headers=auth_headers,
    )
    assert first.status_code == 200, first.text
    assert first.json()["created"] == 1
    assert first.json()["skipped_duplicates"] == 0

    second = await client.post(
        "/api/v1/jobs/import?sources=remoteok&limit_per_source=10",
        headers=auth_headers,
    )
    assert second.status_code == 200, second.text
    assert second.json()["created"] == 0
    assert second.json()["skipped_duplicates"] == 1
