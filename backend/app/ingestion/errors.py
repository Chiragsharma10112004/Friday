from enum import Enum
from typing import Optional


class IngestionErrorCode(str, Enum):
    INVALID_URL = "INVALID_URL"
    SSRF_ATTEMPT_BLOCKED = "SSRF_ATTEMPT_BLOCKED"
    UNSUPPORTED_SOURCE = "UNSUPPORTED_SOURCE"
    SOURCE_ACCESS_RESTRICTED = "SOURCE_ACCESS_RESTRICTED"
    NETWORK_FAILURE = "NETWORK_FAILURE"
    REQUEST_TIMEOUT = "REQUEST_TIMEOUT"
    MALFORMED_PAGE = "MALFORMED_PAGE"
    EXTRACTION_FAILED = "EXTRACTION_FAILED"
    MISSING_JOB_DESCRIPTION = "MISSING_JOB_DESCRIPTION"


class IngestionException(Exception):
    """
    Domain exception for all job ingestion failures.
    """

    def __init__(
        self,
        code: IngestionErrorCode,
        message: str,
        retryable: bool = False,
        source_platform: Optional[str] = None
    ):
        super().__init__(message)
        self.code = code
        self.message = message
        self.retryable = retryable
        self.source_platform = source_platform

