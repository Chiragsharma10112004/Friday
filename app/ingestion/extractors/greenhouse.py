import re
import urllib.parse
from typing import Optional, Tuple
from bs4 import BeautifulSoup

from app.ingestion.extractors.base import BaseJobExtractor
from app.ingestion.schemas import NormalizedJobPosting
from app.ingestion.errors import IngestionErrorCode, IngestionException
from app.ingestion.validators import SafeHttpClient


class GreenhouseExtractor(BaseJobExtractor):
    """
    Extractor for Greenhouse job postings.
    Hierarchy:
    1. Public Greenhouse Board API (authoritative JSON)
    2. JSON-LD Schema.org metadata
    3. Semantic HTML fallback
    """

    @property
    def platform_name(self) -> str:
        return "greenhouse"

    def can_handle(self, url: str, parsed: urllib.parse.ParseResult) -> bool:
        hostname = (parsed.hostname or "").lower()
        if "greenhouse.io" in hostname:
            return True
        if "gh_jid" in parsed.query.lower():
            return True
        return False

    @staticmethod
    def _parse_greenhouse_params(parsed: urllib.parse.ParseResult) -> Tuple[Optional[str], Optional[str]]:
        """
        Extract board token and job id from various Greenhouse URL patterns.
        """
        path_parts = [p for p in parsed.path.strip("/").split("/") if p]
        query_params = urllib.parse.parse_qs(parsed.query)

        board_token = None
        job_id = None

        # Pattern: /embed/job_app?for=company&token=12345
        if "embed" in path_parts or "job_app" in path_parts:
            board_token = query_params.get("for", [None])[0]
            job_id = query_params.get("token", [None])[0]
            if board_token and job_id:
                return board_token, job_id

        # Pattern: /<board_token>/jobs/<job_id>
        if len(path_parts) >= 3 and path_parts[1] == "jobs":
            board_token = path_parts[0]
            job_id = path_parts[2].split("?")[0]
            return board_token, job_id

        # Query param pattern: ?gh_jid=12345
        if "gh_jid" in query_params:
            job_id = query_params["gh_jid"][0]
            # Try to get board token from first path component
            if path_parts:
                board_token = path_parts[0]

        return board_token, job_id

    def extract(self, url: str, parsed: urllib.parse.ParseResult) -> NormalizedJobPosting:
        board_token, job_id = self._parse_greenhouse_params(parsed)

        # ----------------------------------------------------
        # 1. Try Greenhouse Public Board API
        # ----------------------------------------------------
        if board_token and job_id and job_id.isdigit():
            api_url = f"https://boards-api.greenhouse.io/v1/boards/{board_token}/jobs/{job_id}"
            try:
                api_response = SafeHttpClient.get(api_url)
                if api_response.status_code == 200:
                    data = api_response.json()
                    raw_content = data.get("content", "")
                    clean_description = self.clean_html_to_text(raw_content)

                    if clean_description:
                        # Extract departments and offices
                        departments = [d.get("name") for d in data.get("departments", []) if d.get("name")]
                        dept_name = ", ".join(departments) if departments else None
                        
                        location_data = data.get("location", {})
                        location_name = location_data.get("name") if isinstance(location_data, dict) else str(location_data)

                        company_name = board_token.replace("-", " ").replace("_", " ").title()

                        return NormalizedJobPosting(
                            company=company_name,
                            role=data.get("title", "Unknown Role").strip(),
                            job_description=clean_description,
                            source_platform=self.platform_name,
                            source_url=url,
                            location=location_name or None,
                            department=dept_name,
                            job_id=str(data.get("id", job_id)),
                            posted_date=data.get("updated_at"),
                            confidence="high",
                            metadata={
                                "board_token": board_token,
                                "api_used": True,
                                "requisition_id": data.get("requisition_id"),
                            }
                        )
            except Exception:
                # Fall back to HTML scraping if API request fails
                pass

        # ----------------------------------------------------
        # 2. Fetch HTML Page and Try JSON-LD or Semantic HTML
        # ----------------------------------------------------
        page_response = SafeHttpClient.get(url)
        if page_response.status_code != 200:
            raise IngestionException(
                code=IngestionErrorCode.NETWORK_FAILURE,
                message=f"Greenhouse job page returned status code {page_response.status_code}."
            )

        html_text = page_response.text

        # Check JSON-LD
        json_ld = self.find_job_posting_json_ld(html_text)
        if json_ld:
            title = json_ld.get("title", "")
            raw_desc = json_ld.get("description", "")
            clean_desc = self.clean_html_to_text(raw_desc)
            hiring_org = json_ld.get("hiringOrganization", {})
            company = hiring_org.get("name", "") if isinstance(hiring_org, dict) else str(hiring_org)
            if not company and board_token:
                company = board_token.replace("-", " ").title()

            if title and clean_desc:
                loc = None
                job_loc = json_ld.get("jobLocation", {})
                if isinstance(job_loc, dict):
                    addr = job_loc.get("address", {})
                    if isinstance(addr, dict):
                        loc = addr.get("addressLocality") or addr.get("addressRegion") or addr.get("streetAddress")
                    elif isinstance(addr, str):
                        loc = addr

                return NormalizedJobPosting(
                    company=company or "Greenhouse Employer",
                    role=title.strip(),
                    job_description=clean_desc,
                    source_platform=self.platform_name,
                    source_url=url,
                    location=loc,
                    employment_type=json_ld.get("employmentType"),
                    posted_date=json_ld.get("datePosted"),
                    confidence="high",
                    metadata={"json_ld_used": True}
                )

        # Semantic HTML Fallback
        soup = BeautifulSoup(html_text, "html.parser")
        title_tag = soup.select_one(".app-title, .job-title, h1")
        role = title_tag.get_text().strip() if title_tag else "Unknown Role"

        company_tag = soup.select_one(".company-name, .logo-container")
        company = company_tag.get_text().strip() if company_tag else (board_token.replace("-", " ").title() if board_token else "Greenhouse Employer")

        content_tag = soup.select_one("#content, #main, .content, article")
        if not content_tag:
            content_tag = soup.body

        clean_desc = self.clean_html_to_text(str(content_tag)) if content_tag else ""
        if not clean_desc or len(clean_desc) < 30:
            raise IngestionException(
                code=IngestionErrorCode.MISSING_JOB_DESCRIPTION,
                message="Could not extract job description text from Greenhouse posting."
            )

        location_tag = soup.select_one(".location")
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

