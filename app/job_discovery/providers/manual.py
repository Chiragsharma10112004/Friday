from typing import List, Optional
from app.job_discovery.providers.base import BaseJobProvider
from app.job_discovery.schemas import DiscoveredJob, JobSearchQuery
from app.ingestion.service import default_ingestion_service
from app.ingestion.schemas import IngestJobRequest


class ManualUrlProvider(BaseJobProvider):
    """
    Provider that routes manually supplied job URLs through the Phase 2 ingestion engine.
    """

    @property
    def provider_name(self) -> str:
        return "manual"

    def search_jobs(self, query: JobSearchQuery) -> List[DiscoveredJob]:
        discovered: List[DiscoveredJob] = []

        for url in query.include_manual_urls:
            job = self.fetch_job(url)
            if job:
                discovered.append(job)

        return discovered

    def fetch_job(self, job_url_or_id: str) -> Optional[DiscoveredJob]:
        if not job_url_or_id or not job_url_or_id.startswith("http"):
            return None

        try:
            req = IngestJobRequest(job_url=job_url_or_id)
            resp = default_ingestion_service.ingest_job(req)

            if resp.success and resp.data:
                norm = resp.data
                is_remote = False
                if norm.location and "remote" in norm.location.lower():
                    is_remote = True

                return DiscoveredJob(
                    external_id=norm.job_id,
                    provider=norm.source_platform or self.provider_name,
                    source_url=norm.source_url,
                    application_url=norm.source_url,
                    company=norm.company,
                    title=norm.role,
                    location=norm.location,
                    is_remote=is_remote,
                    description=norm.job_description,
                    employment_type=norm.employment_type,
                    posted_at=norm.posted_date,
                    metadata=norm.metadata,
                )
        except Exception:
            return None

        return None
