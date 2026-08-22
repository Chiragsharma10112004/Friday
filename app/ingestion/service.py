import logging
from typing import List, Optional

from app.ingestion.schemas import (
    IngestJobRequest,
    IngestJobResponse,
    NormalizedJobPosting,
    IngestionError,
    IngestionWarning,
)
from app.ingestion.errors import IngestionErrorCode, IngestionException
from app.ingestion.validators import validate_url_syntax
from app.ingestion.detector import PlatformDetector
from app.ingestion.extractors import (
    BaseJobExtractor,
    GreenhouseExtractor,
    LeverExtractor,
    WorkdayExtractor,
    LinkedInExtractor,
    IndeedExtractor,
    GenericExtractor,
)

logger = logging.getLogger("friday.ingestion")


class IngestionService:
    """
    Central orchestration service for job scraping, validation, and normalization.
    """

    def __init__(self):
        # Ordered list of extractors (platform-specific first, generic fallback last)
        self.extractors: List[BaseJobExtractor] = [
            GreenhouseExtractor(),
            LeverExtractor(),
            WorkdayExtractor(),
            LinkedInExtractor(),
            IndeedExtractor(),
            GenericExtractor(),
        ]

    def _select_extractor(self, url: str, parsed, detected_platform: str) -> BaseJobExtractor:
        # First check matching platform name
        for ext in self.extractors:
            if ext.platform_name == detected_platform and ext.can_handle(url, parsed):
                return ext

        # Fallback to any extractor that can handle the URL
        for ext in self.extractors:
            if ext.can_handle(url, parsed):
                return ext

        # Final fallback
        return self.extractors[-1]

    def ingest_job(self, request: IngestJobRequest) -> IngestJobResponse:
        """
        Process a job URL through syntax validation, SSRF checks, platform detection,
        and content extraction. Returns a structured IngestJobResponse.
        """
        url_str = (request.job_url or "").strip()
        detected_platform = None

        try:
            # 1. URL syntax validation
            parsed = validate_url_syntax(url_str)

            # 2. Platform detection
            detected_platform = PlatformDetector.detect(url_str, parsed)

            # 3. Select extractor
            extractor = self._select_extractor(url_str, parsed, detected_platform)

            # 4. Execute extraction
            posting: NormalizedJobPosting = extractor.extract(url_str, parsed)

            # 5. Check for extraction quality warnings
            warnings = []
            if posting.confidence in ("medium", "low"):
                warnings.append(
                    IngestionWarning(
                        code="INFERRED_FIELDS_PRESENT",
                        message=f"Extraction confidence is {posting.confidence}. Please review extracted role and company name before applying."
                    )
                )

            return IngestJobResponse(
                success=True,
                source_platform=posting.source_platform or detected_platform,
                data=posting,
                warnings=warnings,
                errors=[]
            )

        except IngestionException as e:
            logger.info("Ingestion controlled error for '%s' [%s]: %s", url_str, e.code, e.message)
            return IngestJobResponse(
                success=False,
                source_platform=e.source_platform or detected_platform,
                data=None,
                warnings=[],
                errors=[
                    IngestionError(
                        code=e.code,
                        message=e.message,
                        retryable=e.retryable
                    )
                ]
            )
        except Exception as e:
            logger.error("Unexpected ingestion error for '%s': %s", url_str, str(e), exc_info=True)
            return IngestJobResponse(
                success=False,
                source_platform=detected_platform or "unknown",
                data=None,
                warnings=[],
                errors=[
                    IngestionError(
                        code=IngestionErrorCode.EXTRACTION_FAILED,
                        message="An unexpected error occurred while extracting the job posting. Please try copying the job description text directly.",
                        retryable=False
                    )
                ]
            )


# Default singleton instance
default_ingestion_service = IngestionService()

