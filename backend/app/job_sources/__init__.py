"""Public job-source adapters used by JOB_HUNT V1."""
from app.job_sources.base import ExternalJob
from app.job_sources.remoteok import fetch_remoteok_jobs
from app.job_sources.wwr import fetch_wwr_jobs

__all__ = ["ExternalJob", "fetch_remoteok_jobs", "fetch_wwr_jobs"]
