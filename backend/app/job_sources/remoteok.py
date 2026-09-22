"""Remote OK public JSON feed adapter.

Official public feed: https://remoteok.com/api
"""
from __future__ import annotations

from collections.abc import Iterable
from typing import Any

import httpx

from app.job_sources.base import ExternalJob
from app.models.job_opportunity import Modality

REMOTE_OK_URL = "https://remoteok.com/api"
_HEADERS = {
    "Accept": "application/json",
    "User-Agent": "JobOpsAI/1.0 (+https://github.com/Arcan17/jobops-ai)",
}


def _text(value: Any) -> str:
    return str(value or "").strip()


def normalize_remoteok_item(item: dict[str, Any]) -> ExternalJob | None:
    company = _text(item.get("company"))
    role = _text(item.get("position"))
    link = _text(item.get("url") or item.get("apply_url"))
    if not company or not role or not link:
        # The feed currently includes a metadata/legal object before jobs.
        return None

    raw_tags = item.get("tags") or []
    tags: tuple[str, ...]
    if isinstance(raw_tags, list):
        tags = tuple(_text(tag) for tag in raw_tags if _text(tag))
    else:
        tags = ()

    location = _text(item.get("location")) or None
    external_id = _text(item.get("id")) or link

    return ExternalJob(
        source="remoteok",
        external_id=external_id,
        link=link,
        company=company,
        role_title=role,
        description=_text(item.get("description")),
        stack=tags,
        requirements="",
        modality=Modality.remote,
        country=location,
        salary=None,  # Currency is not explicit enough for the current JobOps schema.
    )


def parse_remoteok_payload(payload: Any) -> list[ExternalJob]:
    if not isinstance(payload, list):
        return []
    jobs: list[ExternalJob] = []
    seen: set[str] = set()
    for raw in payload:
        if not isinstance(raw, dict):
            continue
        job = normalize_remoteok_item(raw)
        if job is None or job.link in seen:
            continue
        seen.add(job.link)
        jobs.append(job)
    return jobs


async def fetch_remoteok_jobs(limit: int = 25) -> list[ExternalJob]:
    safe_limit = max(1, min(limit, 100))
    async with httpx.AsyncClient(timeout=20.0, follow_redirects=True) as client:
        response = await client.get(REMOTE_OK_URL, headers=_HEADERS)
        response.raise_for_status()
        return parse_remoteok_payload(response.json())[:safe_limit]
