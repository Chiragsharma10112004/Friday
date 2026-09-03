from enum import Enum
from typing import Optional, Dict, Any


class FeedbackErrorCode(str, Enum):
    FEEDBACK_NOT_FOUND = "FEEDBACK_NOT_FOUND"
    APPLICATION_NOT_FOUND = "APPLICATION_NOT_FOUND"
    ASSET_VERSION_NOT_FOUND = "ASSET_VERSION_NOT_FOUND"
    FIELD_ISSUE_NOT_FOUND = "FIELD_ISSUE_NOT_FOUND"
    INVALID_OUTCOME = "INVALID_OUTCOME"
    INVALID_STAGE = "INVALID_STAGE"
    DUPLICATE_OUTCOME = "DUPLICATE_OUTCOME"
    INVALID_SCORE = "INVALID_SCORE"
    OPERATION_FAILED = "OPERATION_FAILED"


class FeedbackException(Exception):
    """Domain exception for Phase 8 Application Feedback operations."""

    def __init__(
        self,
        code: FeedbackErrorCode,
        message: str,
        application_id: Optional[int] = None,
        feedback_id: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        self.code = code
        self.message = message
        self.application_id = application_id
        self.feedback_id = feedback_id
        self.details = details or {}
        super().__init__(self.message)
