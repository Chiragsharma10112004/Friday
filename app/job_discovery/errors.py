from enum import Enum
from typing import Optional


class DiscoveryErrorCode(str, Enum):
    PROFILE_NOT_FOUND = "PROFILE_NOT_FOUND"
    PROVIDER_UNSUPPORTED = "PROVIDER_UNSUPPORTED"
    PROVIDER_UNAVAILABLE = "PROVIDER_UNAVAILABLE"
    INVALID_SEARCH_REQUEST = "INVALID_SEARCH_REQUEST"
    INVALID_JOB_URL = "INVALID_JOB_URL"
    JOB_ACCESS_RESTRICTED = "JOB_ACCESS_RESTRICTED"
    JOB_NOT_FOUND = "JOB_NOT_FOUND"
    OPPORTUNITY_NOT_FOUND = "OPPORTUNITY_NOT_FOUND"
    INVALID_STATUS_TRANSITION = "INVALID_STATUS_TRANSITION"
    DISCOVERY_FAILED = "DISCOVERY_FAILED"
    INGESTION_FAILED = "INGESTION_FAILED"
    DUPLICATE_OPPORTUNITY = "DUPLICATE_OPPORTUNITY"
    INTERNAL_ERROR = "INTERNAL_ERROR"


class DiscoveryException(Exception):
    """
    Domain exception for Job Discovery & Opportunity Pipeline operations.
    """

    def __init__(
        self,
        code: DiscoveryErrorCode,
        message: str,
        retryable: bool = False,
        provider: Optional[str] = None
    ):
        super().__init__(message)
        self.code = code
        self.message = message
        self.retryable = retryable
        self.provider = provider
