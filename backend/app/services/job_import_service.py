"""Import public job feeds into the existing JobOps opportunity model."""
from __future__ import annotations

from collections.abc import Awaitable, Callable
from enum import StrEnum

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.job_sources import ExternalJob, fetch_remoteok_jobs, fetch_wwr_jobs
from app.models.job_opportunity import JobOpportunity
from app.models.profile import Profile
from app.schemas.job import JobRead
from app.schemas.job_import import JobImportResponse, JobImportSourceResult
from app.services import job_service


class JobSource(StrEnum):
    remoteok = "remoteok"
    wwr = "wwr"


Fetcher = Callable[[int], Awaitable[list[ExternalJob]]]

FETCHERS: dict[JobSource, Fetcher] = {
    JobSource.remoteok: fetch_remoteok_jobs,
    JobSource.wwr: fetch_wwr_jobs,
}


async def _existing_links(
    db: AsyncSession,
    profile: Profile,
    links: list[str],
) -> set[str]:
    if not links:
        return set()
    rows = await db.scalars(
        select(JobOpportunity.link).where(
            JobOpportunity.profile_id == profile.id,
            JobOpportunity.link.in_(links),
        )
    )
    return {link for link in rows if link}


async def import_jobs(
    db: AsyncSession,
    profile: Profile,
    sources: list[JobSource],
    *,
    limit_per_source: int = 25,
) -> JobImportResponse:
    safe_limit = max(1, min(limit_per_source, 100))
    source_results: list[JobImportSourceResult] = []

    total_fetched = 0
    total_created = 0
    total_skipped = 0

    for source in sources:
        external_jobs = await FETCHERS[source](safe_limit)
        total_fetched += len(external_jobs)

        existing = await _existing_links(
            db,
            profile,
            [job.link for job in external_jobs],
        )
        created_jobs: list[JobRead] = []
        skipped = 0

        # Also dedupe duplicates that appear inside the same fetched batch.
        batch_seen = set(existing)
        for external in external_jobs:
            if external.link in batch_seen:
                skipped += 1
                continue
            batch_seen.add(external.link)
            created = await job_service.create_job(
                db,
                profile,
                external.to_job_create(),
            )
            created_jobs.append(JobRead.model_validate(created))

        created_count = len(created_jobs)
        total_created += created_count
        total_skipped += skipped
        source_results.append(
            JobImportSourceResult(
                source=source.value,
                fetched=len(external_jobs),
                created=created_count,
                skipped_duplicates=skipped,
                jobs=created_jobs,
            )
        )

    return JobImportResponse(
        fetched=total_fetched,
        created=total_created,
        skipped_duplicates=total_skipped,
        sources=source_results,
    )
