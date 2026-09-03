import re
import urllib.parse
from typing import List, Optional
from bs4 import BeautifulSoup

from app.job_discovery.providers.base import BaseJobProvider
from app.job_discovery.schemas import DiscoveredJob, JobSearchQuery
from app.ingestion.validators import SafeHttpClient
from app.ingestion.extractors.greenhouse import GreenhouseExtractor


class GreenhouseDiscoveryProvider(BaseJobProvider):
    """
    Job discovery provider for public Greenhouse job boards.
    """

    DEFAULT_COMPANIES = ["anthropic", "scaleai", "figma", "stripe", "openai", "canonical"]

    @property
    def provider_name(self) -> str:
        return "greenhouse"

    @staticmethod
    def _clean_html(html_str: str) -> str:
        if not html_str:
            return ""
        soup = BeautifulSoup(html_str, "html.parser")
        return soup.get_text(separator="\n", strip=True)

    def search_jobs(self, query: JobSearchQuery) -> List[DiscoveredJob]:
        companies_to_search = query.companies if query.companies else self.DEFAULT_COMPANIES
        discovered: List[DiscoveredJob] = []

        for company_slug in companies_to_search:
            clean_slug = company_slug.strip().lower()
            api_url = f"https://boards-api.greenhouse.io/v1/boards/{clean_slug}/jobs?content=true"

            try:
                response = SafeHttpClient.get(api_url)
                if response.status_code != 200:
                    continue

                data = response.json()
                jobs_list = data.get("jobs", [])

                for item in jobs_list:
                    job_id = str(item.get("id", ""))
                    title = item.get("title", "").strip()
                    location_obj = item.get("location", {})
                    location_name = location_obj.get("name", "") if isinstance(location_obj, dict) else str(location_obj)

                    raw_content = item.get("content", "")
                    clean_desc = self._clean_html(raw_content)
                    if not clean_desc or len(clean_desc) < 30:
                        clean_desc = f"{title} at {clean_slug.title()}"

                    abs_url = item.get("absolute_url") or f"https://boards.greenhouse.io/{clean_slug}/jobs/{job_id}"
                    
                    is_remote = False
                    if "remote" in location_name.lower() or "remote" in title.lower():
                        is_remote = True

                    discovered.append(
                        DiscoveredJob(
                            external_id=job_id,
                            provider=self.provider_name,
                            source_url=abs_url,
                            application_url=abs_url,
                            company=clean_slug.replace("-", " ").title(),
                            title=title,
                            location=location_name or ("Remote" if is_remote else None),
                            is_remote=is_remote,
                            description=clean_desc,
                            posted_at=str(item.get("updated_at", "")),
                            metadata={"greenhouse_board": clean_slug, "internal_job_id": job_id}
                        )
                    )

            except Exception:
                continue

        return discovered

    def fetch_job(self, job_url_or_id: str) -> Optional[DiscoveredJob]:
        if job_url_or_id.startswith("http"):
            parsed = urllib.parse.urlparse(job_url_or_id)
            extractor = GreenhouseExtractor()
            if extractor.can_handle(job_url_or_id, parsed):
                normalized = extractor.extract(job_url_or_id, parsed)
                return DiscoveredJob(
                    external_id=normalized.job_id,
                    provider=self.provider_name,
                    source_url=normalized.source_url,
                    application_url=normalized.source_url,
                    company=normalized.company,
                    title=normalized.role,
                    location=normalized.location,
                    is_remote="remote" in (normalized.location or "").lower(),
                    description=normalized.job_description,
                    employment_type=normalized.employment_type,
                    posted_at=normalized.posted_date,
                    metadata=normalized.metadata,
                )
        return None
