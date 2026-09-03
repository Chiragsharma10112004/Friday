import re
import urllib.parse
from typing import Optional, Tuple
from bs4 import BeautifulSoup

from app.ingestion.extractors.base import BaseJobExtractor
from app.ingestion.schemas import NormalizedJobPosting
from app.ingestion.errors import IngestionErrorCode, IngestionException
from app.ingestion.validators import SafeHttpClient


class LeverExtractor(BaseJobExtractor):
    """
    Extractor for Lever job postings.
    Hierarchy:
    1. Public Lever Postings API (authoritative structured JSON)
    2. JSON-LD Schema.org metadata
    3. Semantic HTML fallback
    """

    @property
    def platform_name(self) -> str:
        return "lever"

    def can_handle(self, url: str, parsed: urllib.parse.ParseResult) -> bool:
        hostname = (parsed.hostname or "").lower()
        return "lever.co" in hostname

    @staticmethod
    def _parse_lever_params(parsed: urllib.parse.ParseResult) -> Tuple[Optional[str], Optional[str]]:
        """
        Extract company slug and posting id from Lever URL.
        Pattern: jobs.lever.co/<company>/<job_id>
        """
        path_parts = [p for p in parsed.path.strip("/").split("/") if p]
        if len(path_parts) >= 2:
            company = path_parts[0]
            job_id = path_parts[1].split("?")[0]
            return company, job_id
        return None, None

    def extract(self, url: str, parsed: urllib.parse.ParseResult) -> NormalizedJobPosting:
        company_slug, job_id = self._parse_lever_params(parsed)

        # ----------------------------------------------------
        # 1. Try Lever Public Postings API
        # ----------------------------------------------------
        if company_slug and job_id:
            api_url = f"https://api.lever.co/v0/postings/{company_slug}/{job_id}"
            try:
                api_response = SafeHttpClient.get(api_url)
                if api_response.status_code == 200:
                    data = api_response.json()
                    
                    description = data.get("descriptionPlain") or self.clean_html_to_text(data.get("description", ""))
                    
                    # Extract list items (Requirements, responsibilities, etc.)
                    requirements = []
                    responsibilities = []
                    extra_sections = []
                    for section in data.get("lists", []):
                        sec_title = section.get("text", "")
                        sec_content = self.clean_html_to_text(section.get("content", ""))
                        if "require" in sec_title.lower() or "qualif" in sec_title.lower():
                            requirements.append(f"{sec_title}:\n{sec_content}")
                        elif "responsib" in sec_title.lower() or "what you'll do" in sec_title.lower():
                            responsibilities.append(f"{sec_title}:\n{sec_content}")
                        else:
                            extra_sections.append(f"{sec_title}:\n{sec_content}")

                    full_desc_parts = [description]
                    if responsibilities:
                        full_desc_parts.extend(responsibilities)
                    if requirements:
                        full_desc_parts.extend(requirements)
                    if extra_sections:
                        full_desc_parts.extend(extra_sections)

                    additional = data.get("additionalPlain") or self.clean_html_to_text(data.get("additional", ""))
                    if additional:
                        full_desc_parts.append(additional)

                    full_description = "\n\n".join(part for part in full_desc_parts if part).strip()
                    
                    categories = data.get("categories", {})
                    company_name = company_slug.replace("-", " ").title()

                    return NormalizedJobPosting(
                        company=company_name,
                        role=data.get("text", "Unknown Role").strip(),
                        job_description=full_description,
                        source_platform=self.platform_name,
                        source_url=url,
                        location=categories.get("location"),
                        department=categories.get("team") or categories.get("department"),
                        employment_type=categories.get("commitment"),
                        workplace_type=categories.get("workplaceType"),
                        posted_date=str(data.get("createdAt", "")) if data.get("createdAt") else None,
                        job_id=job_id,
                        confidence="high",
                        metadata={
                            "company_slug": company_slug,
                            "api_used": True,
                            "salary_range": data.get("salaryRange")
                        }
                    )
            except Exception:
                pass

        # ----------------------------------------------------
        # 2. Fetch HTML Page Fallback
        # ----------------------------------------------------
        page_response = SafeHttpClient.get(url)
        if page_response.status_code != 200:
            raise IngestionException(
                code=IngestionErrorCode.NETWORK_FAILURE,
                message=f"Lever job page returned status code {page_response.status_code}."
            )

        html_text = page_response.text

        # Check JSON-LD
        json_ld = self.find_job_posting_json_ld(html_text)
        if json_ld:
            title = json_ld.get("title", "")
            clean_desc = self.clean_html_to_text(json_ld.get("description", ""))
            hiring_org = json_ld.get("hiringOrganization", {})
            company = hiring_org.get("name", "") if isinstance(hiring_org, dict) else str(hiring_org)
            if not company and company_slug:
                company = company_slug.replace("-", " ").title()

            if title and clean_desc:
                return NormalizedJobPosting(
                    company=company or "Lever Employer",
                    role=title.strip(),
                    job_description=clean_desc,
                    source_platform=self.platform_name,
                    source_url=url,
                    confidence="high",
                    metadata={"json_ld_used": True}
                )

        # Semantic HTML Fallback
        soup = BeautifulSoup(html_text, "html.parser")
        title_tag = soup.select_one(".posting-headline h2, h2, h1")
        role = title_tag.get_text().strip() if title_tag else "Unknown Role"

        company = company_slug.replace("-", " ").title() if company_slug else "Lever Employer"

        content_tag = soup.select_one(".section-page, .content, main, body")
        clean_desc = self.clean_html_to_text(str(content_tag)) if content_tag else ""

        if not clean_desc or len(clean_desc) < 30:
            raise IngestionException(
                code=IngestionErrorCode.MISSING_JOB_DESCRIPTION,
                message="Could not extract job description text from Lever posting."
            )

        location_tag = soup.select_one(".location, .posting-categories .sort-by-time")
        location = location_tag.get_text().strip() if location_tag else None

        return NormalizedJobPosting(
            company=company,
            role=role,
            job_description=clean_desc,
            source_platform=self.platform_name,
            source_url=url,
            location=location,
            job_id=job_id,
            confidence="medium",
            metadata={"html_fallback_used": True}
        )

