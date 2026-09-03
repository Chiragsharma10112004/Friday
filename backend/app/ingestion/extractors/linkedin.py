import urllib.parse

from app.ingestion.extractors.base import BaseJobExtractor
from app.ingestion.schemas import NormalizedJobPosting
from app.ingestion.errors import IngestionErrorCode, IngestionException


class LinkedInExtractor(BaseJobExtractor):
    """
    Extractor for LinkedIn job postings.
    Per ethical and security policies, FRIDAY does not attempt to bypass LinkedIn
    authentication, rate limiting, bot protection, or session walls.
    Returns a clear SOURCE_ACCESS_RESTRICTED domain notice.
    """

    @property
    def platform_name(self) -> str:
        return "linkedin"

    def can_handle(self, url: str, parsed: urllib.parse.ParseResult) -> bool:
        hostname = (parsed.hostname or "").lower()
        return "linkedin.com" in hostname

    def extract(self, url: str, parsed: urllib.parse.ParseResult) -> NormalizedJobPosting:
        raise IngestionException(
            code=IngestionErrorCode.SOURCE_ACCESS_RESTRICTED,
            message=(
                "LinkedIn job postings require user authentication and actively restrict automated scraping. "
                "To analyze this position safely, please copy and paste the job description text directly into FRIDAY."
            ),
            retryable=False,
            source_platform=self.platform_name
        )

