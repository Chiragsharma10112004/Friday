from enum import Enum
from typing import Optional


class AutomationErrorCode(str, Enum):
    PROFILE_NOT_FOUND = "PROFILE_NOT_FOUND"
    APPLICATION_NOT_FOUND = "APPLICATION_NOT_FOUND"
    INVALID_APPLICATION_URL = "INVALID_APPLICATION_URL"
    UNSUPPORTED_PLATFORM = "UNSUPPORTED_PLATFORM"
    SOURCE_ACCESS_RESTRICTED = "SOURCE_ACCESS_RESTRICTED"
    BROWSER_UNAVAILABLE = "BROWSER_UNAVAILABLE"
    BROWSER_TIMEOUT = "BROWSER_TIMEOUT"
    INSPECTION_FAILED = "INSPECTION_FAILED"
    SESSION_NOT_FOUND = "SESSION_NOT_FOUND"
    SESSION_EXPIRED = "SESSION_EXPIRED"
    PAGE_STATE_CHANGED = "PAGE_STATE_CHANGED"
    STAGE_TRANSITION_INVALID = "STAGE_TRANSITION_INVALID"
    FIELD_NOT_FOUND = "FIELD_NOT_FOUND"
    FIELD_NOT_APPROVED = "FIELD_NOT_APPROVED"
    UNSAFE_FIELD = "UNSAFE_FIELD"
    MANUAL_INPUT_REQUIRED = "MANUAL_INPUT_REQUIRED"
    UNSUPPORTED_FIELD = "UNSUPPORTED_FIELD"
    ASSET_FILE_NOT_AVAILABLE = "ASSET_FILE_NOT_AVAILABLE"
    CAPTCHA_DETECTED = "CAPTCHA_DETECTED"
    AUTHENTICATION_REQUIRED = "AUTHENTICATION_REQUIRED"
    ACCOUNT_CREATION_REQUIRED = "ACCOUNT_CREATION_REQUIRED"
    EMAIL_VERIFICATION_REQUIRED = "EMAIL_VERIFICATION_REQUIRED"
    FORM_NOT_READY = "FORM_NOT_READY"
    SUBMISSION_BLOCKED = "SUBMISSION_BLOCKED"


class AutomationException(Exception):
    """
    Domain exception for all application automation inspection and filling operations.
    """

    def __init__(
        self,
        code: AutomationErrorCode,
        message: str,
        retryable: bool = False,
        platform: Optional[str] = None
    ):
        super().__init__(message)
        self.code = code
        self.message = message
        self.retryable = retryable
        self.platform = platform
