import urllib.parse

from app.ingestion.extractors.base import BaseJobExtractor
from app.ingestion.schemas import NormalizedJobPosting
from app.ingestion.errors import IngestionErrorCode, IngestionException


class IndeedExtractor(BaseJobExtractor):
    """
    Extractor for Indeed job postings.
    Per ethical and security policies, FRIDAY does not attempt to bypass Indeed
    Cloudflare protections, CAPTCHAs, or authentication walls.
    Returns a clear SOURCE_ACCESS_RESTRICTED domain notice.
    """

    @property
    def platform_name(self) -> str:
        return "indeed"

    def can_handle(self, url: str, parsed: urllib.parse.ParseResult) -> bool:
        hostname = (parsed.hostname or "").lower()
        return "indeed." in hostname

    def extract(self, url: str, parsed: urllib.parse.ParseResult) -> NormalizedJobPosting:
        raise IngestionException(
            code=IngestionErrorCode.SOURCE_ACCESS_RESTRICTED,
            message=(
                "Indeed job postings utilize strict anti-bot verification and access restrictions. "
                "To analyze this role safely, please copy and paste the job description text directly into FRIDAY."
            ),
            retryable=False,
            source_platform=self.platform_name
        )

