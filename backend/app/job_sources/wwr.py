"""We Work Remotely public RSS adapter.

Official public feed:
https://weworkremotely.com/categories/remote-back-end-programming-jobs.rss
"""
from __future__ import annotations

import html
import re
import xml.etree.ElementTree as ET

import httpx

from app.job_sources.base import ExternalJob
from app.models.job_opportunity import Modality

WWR_BACKEND_RSS_URL = (
    "https://weworkremotely.com/categories/remote-back-end-programming-jobs.rss"
)
_HEADERS = {
    "Accept": "application/rss+xml, application/xml, text/xml",
    "User-Agent": "JobOpsAI/1.0 (+https://github.com/Arcan17/jobops-ai)",
}
_TAG_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"\s+")


def _clean_html(value: str | None) -> str:
    text = html.unescape(value or "")
    text = _TAG_RE.sub(" ", text)
    return _WS_RE.sub(" ", text).strip()


def _split_title(title: str) -> tuple[str, str]:
    cleaned = title.strip()
    if ":" not in cleaned:
        return "Unknown", cleaned
    company, role = cleaned.split(":", 1)
    return company.strip() or "Unknown", role.strip() or cleaned


def parse_wwr_rss(payload: str) -> list[ExternalJob]:
    try:
        root = ET.fromstring(payload)
    except ET.ParseError:
        return []

    jobs: list[ExternalJob] = []
    seen: set[str] = set()
    for item in root.findall(".//item"):
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        if not title or not link or link in seen:
            continue

        company, role = _split_title(title)
        description = _clean_html(item.findtext("description"))
        categories = tuple(
            value.strip()
            for value in (node.text or "" for node in item.findall("category"))
            if value.strip()
        )

        seen.add(link)
        jobs.append(
            ExternalJob(
                source="wwr",
                external_id=(item.findtext("guid") or link).strip(),
                link=link,
                company=company,
                role_title=role,
                description=description,
                stack=categories,
                requirements="",
                modality=Modality.remote,
                country=None,
                salary=None,
            )
        )
    return jobs


async def fetch_wwr_jobs(limit: int = 25) -> list[ExternalJob]:
    safe_limit = max(1, min(limit, 100))
    async with httpx.AsyncClient(timeout=20.0, follow_redirects=True) as client:
        response = await client.get(WWR_BACKEND_RSS_URL, headers=_HEADERS)
        response.raise_for_status()
        return parse_wwr_rss(response.text)[:safe_limit]
