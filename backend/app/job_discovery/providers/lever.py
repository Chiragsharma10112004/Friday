import urllib.parse
from typing import List, Optional
from bs4 import BeautifulSoup

from app.job_discovery.providers.base import BaseJobProvider
from app.job_discovery.schemas import DiscoveredJob, JobSearchQuery
from app.ingestion.validators import SafeHttpClient
from app.ingestion.extractors.lever import LeverExtractor


class LeverDiscoveryProvider(BaseJobProvider):
    """
    Job discovery provider for public Lever job boards.
    """

    DEFAULT_COMPANIES = ["palantir", "netflix", "affirm", "spotify", "duolingo", "datadog"]

    @property
    def provider_name(self) -> str:
        return "lever"

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
            api_url = f"https://api.lever.co/v0/postings/{clean_slug}?mode=json"

            try:
                response = SafeHttpClient.get(api_url)
                if response.status_code != 200:
                    continue

                jobs_list = response.json()
                if not isinstance(jobs_list, list):
                    continue

                for item in jobs_list:
                    job_id = str(item.get("id", ""))
                    title = item.get("text", "").strip()
                    categories = item.get("categories", {})
                    location_name = categories.get("location", "")
                    commitment = categories.get("commitment", "")

                    raw_desc = item.get("descriptionPlain") or self._clean_html(item.get("description", ""))
                    if not raw_desc or len(raw_desc) < 30:
                        raw_desc = f"{title} at {clean_slug.title()}"

                    hosted_url = item.get("hostedUrl") or f"https://jobs.lever.co/{clean_slug}/{job_id}"
                    apply_url = item.get("applyUrl") or f"{hosted_url}/apply"

                    is_remote = False
                    workplace_type = categories.get("workplaceType", "")
                    if "remote" in location_name.lower() or "remote" in workplace_type.lower() or "remote" in title.lower():
                        is_remote = True

                    discovered.append(
                        DiscoveredJob(
                            external_id=job_id,
                            provider=self.provider_name,
                            source_url=hosted_url,
                            application_url=apply_url,
                            company=clean_slug.replace("-", " ").title(),
                            title=title,
                            location=location_name or ("Remote" if is_remote else None),
                            is_remote=is_remote,
                            description=raw_desc,
                            employment_type=commitment or None,
                            posted_at=str(item.get("createdAt", "")),
                            metadata={"lever_slug": clean_slug, "internal_job_id": job_id}
                        )
                    )

            except Exception:
                continue

        return discovered

    def fetch_job(self, job_url_or_id: str) -> Optional[DiscoveredJob]:
        if job_url_or_id.startswith("http"):
            parsed = urllib.parse.urlparse(job_url_or_id)
            extractor = LeverExtractor()
            if extractor.can_handle(job_url_or_id, parsed):
                normalized = extractor.extract(job_url_or_id, parsed)
                return DiscoveredJob(
                    external_id=normalized.job_id,
                    provider=self.provider_name,
                    source_url=normalized.source_url,
                    application_url=f"{normalized.source_url}/apply" if "jobs.lever.co" in normalized.source_url else normalized.source_url,
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
