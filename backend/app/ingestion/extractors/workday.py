import urllib.parse
from bs4 import BeautifulSoup

from app.ingestion.extractors.base import BaseJobExtractor
from app.ingestion.schemas import NormalizedJobPosting
from app.ingestion.errors import IngestionErrorCode, IngestionException
from app.ingestion.validators import SafeHttpClient


class WorkdayExtractor(BaseJobExtractor):
    """
    Extractor for Workday career portal postings.
    Extracts publicly server-rendered JSON-LD schema when available,
    otherwise returns a structured SOURCE_ACCESS_RESTRICTED error.
    """

    @property
    def platform_name(self) -> str:
        return "workday"

    def can_handle(self, url: str, parsed: urllib.parse.ParseResult) -> bool:
        hostname = (parsed.hostname or "").lower()
        return "myworkdayjobs.com" in hostname or "workday.com" in hostname

    def extract(self, url: str, parsed: urllib.parse.ParseResult) -> NormalizedJobPosting:
        try:
            response = SafeHttpClient.get(url)
        except IngestionException:
            raise
        except Exception as e:
            raise IngestionException(
                code=IngestionErrorCode.NETWORK_FAILURE,
                message=f"Could not connect to Workday portal: {str(e)}",
                source_platform=self.platform_name
            )

        if response.status_code != 200:
            raise IngestionException(
                code=IngestionErrorCode.SOURCE_ACCESS_RESTRICTED,
                message=(
                    f"Workday returned status code {response.status_code}. Workday postings typically require dynamic "
                    "client-side rendering or active session headers. Please copy and paste the job description directly."
                ),
                source_platform=self.platform_name
            )

        html_text = response.text

        # 1. Attempt to parse server-rendered JSON-LD
        json_ld = self.find_job_posting_json_ld(html_text)
        if json_ld:
            title = json_ld.get("title", "")
            clean_desc = self.clean_html_to_text(json_ld.get("description", ""))
            hiring_org = json_ld.get("hiringOrganization", {})
            company = hiring_org.get("name", "") if isinstance(hiring_org, dict) else str(hiring_org)

            if title and clean_desc and len(clean_desc) > 50:
                return NormalizedJobPosting(
                    company=company or "Workday Employer",
                    role=title.strip(),
                    job_description=clean_desc,
                    source_platform=self.platform_name,
                    source_url=url,
                    confidence="high",
                    metadata={"json_ld_used": True}
                )

        # 2. If no server-rendered description was found (typical for Workday React/SPA clients)
        raise IngestionException(
            code=IngestionErrorCode.SOURCE_ACCESS_RESTRICTED,
            message=(
                "This Workday job posting requires client-side JavaScript rendering to display full details. "
                "To analyze this role, please copy and paste the job description text directly into FRIDAY."
            ),
            source_platform=self.platform_name
        )

