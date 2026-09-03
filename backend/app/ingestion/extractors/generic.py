import urllib.parse
from bs4 import BeautifulSoup

from app.ingestion.extractors.base import BaseJobExtractor
from app.ingestion.schemas import NormalizedJobPosting
from app.ingestion.errors import IngestionErrorCode, IngestionException
from app.ingestion.validators import SafeHttpClient


class GenericExtractor(BaseJobExtractor):
    """
    Fallback extractor for arbitrary company career pages and job boards.
    Hierarchy:
    1. Schema.org JobPosting JSON-LD (High confidence)
    2. OpenGraph metadata tags (Medium confidence)
    3. Semantic HTML main/article content parsing (Medium/Low confidence)
    """

    @property
    def platform_name(self) -> str:
        return "generic"

    def can_handle(self, url: str, parsed: urllib.parse.ParseResult) -> bool:
        return True  # Fallback extractor handles any valid HTTP/HTTPS URL

    def extract(self, url: str, parsed: urllib.parse.ParseResult) -> NormalizedJobPosting:
        response = SafeHttpClient.get(url)
        if response.status_code != 200:
            raise IngestionException(
                code=IngestionErrorCode.NETWORK_FAILURE,
                message=f"Target page returned HTTP status {response.status_code}.",
                source_platform=self.platform_name
            )

        html_text = response.text
        if not html_text or not html_text.strip():
            raise IngestionException(
                code=IngestionErrorCode.MALFORMED_PAGE,
                message="Target page returned an empty response body.",
                source_platform=self.platform_name
            )

        # ----------------------------------------------------
        # 1. Check for Schema.org JobPosting JSON-LD
        # ----------------------------------------------------
        json_ld = self.find_job_posting_json_ld(html_text)
        if json_ld:
            title = json_ld.get("title", "")
            raw_desc = json_ld.get("description", "")
            clean_desc = self.clean_html_to_text(raw_desc)
            
            hiring_org = json_ld.get("hiringOrganization", {})
            company = hiring_org.get("name", "") if isinstance(hiring_org, dict) else str(hiring_org)

            if title and clean_desc and len(clean_desc) > 30:
                loc = None
                job_loc = json_ld.get("jobLocation", {})
                if isinstance(job_loc, dict):
                    addr = job_loc.get("address", {})
                    if isinstance(addr, dict):
                        loc_parts = [addr.get("addressLocality"), addr.get("addressRegion"), addr.get("addressCountry")]
                        loc = ", ".join(p for p in loc_parts if p)
                    elif isinstance(addr, str):
                        loc = addr

                # Salary range
                salary_str = None
                base_salary = json_ld.get("baseSalary", {})
                if isinstance(base_salary, dict):
                    value = base_salary.get("value", {})
                    if isinstance(value, dict):
                        min_val = value.get("minValue")
                        max_val = value.get("maxValue")
                        curr = base_salary.get("currency", "USD")
                        if min_val and max_val:
                            salary_str = f"{curr} {min_val} - {max_val}"
                    elif isinstance(value, (int, float, str)):
                        salary_str = str(value)

                domain_company = (parsed.hostname or "").split(".")[0].capitalize()
                return NormalizedJobPosting(
                    company=company or domain_company or "Hiring Company",
                    role=title.strip(),
                    job_description=clean_desc,
                    source_platform=self.platform_name,
                    source_url=url,
                    location=loc,
                    employment_type=json_ld.get("employmentType"),
                    salary_range=salary_str,
                    posted_date=json_ld.get("datePosted"),
                    confidence="high",
                    metadata={"json_ld_used": True}
                )

        # ----------------------------------------------------
        # 2. Semantic HTML & OpenGraph Extraction
        # ----------------------------------------------------
        soup = BeautifulSoup(html_text, "html.parser")

        # Extract Title
        role = None
        og_title = soup.find("meta", property="og:title")
        if og_title and og_title.get("content"):
            role = og_title["content"].strip()
        if not role:
            h1 = soup.find("h1")
            if h1:
                role = h1.get_text().strip()
        if not role and soup.title:
            role = soup.title.get_text().split("-")[0].split("|")[0].strip()

        # Extract Company
        company = None
        og_site = soup.find("meta", property="og:site_name")
        if og_site and og_site.get("content"):
            company = og_site["content"].strip()
        if not company:
            # Fall back to root hostname domain
            host_parts = (parsed.hostname or "").split(".")
            if len(host_parts) >= 2:
                company = host_parts[-2].capitalize()
            else:
                company = (parsed.hostname or "Hiring Organization").capitalize()

        # Extract Main Content
        content_candidates = soup.select(
            "[class*='job-description'], [class*='job-detail'], [id*='job-description'], "
            "[class*='career-description'], main, article"
        )
        target_container = content_candidates[0] if content_candidates else (soup.find("body") or soup)
        clean_desc = self.clean_html_to_text(str(target_container))

        if not clean_desc or len(clean_desc) < 40:
            # Try OpenGraph description as final fallback
            og_desc = soup.find("meta", property="og:description") or soup.find("meta", attrs={"name": "description"})
            if og_desc and og_desc.get("content") and len(og_desc["content"]) > 30:
                clean_desc = og_desc["content"].strip()
            else:
                raise IngestionException(
                    code=IngestionErrorCode.MISSING_JOB_DESCRIPTION,
                    message="Could not locate or extract job description content from this page.",
                    source_platform=self.platform_name
                )

        return NormalizedJobPosting(
            company=company or "Hiring Organization",
            role=role or "Open Position",
            job_description=clean_desc,
            source_platform=self.platform_name,
            source_url=url,
            confidence="medium" if (role and company) else "low",
            metadata={"html_semantic_used": True}
        )

