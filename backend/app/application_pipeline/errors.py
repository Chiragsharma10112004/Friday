from enum import Enum
from typing import Optional


class PipelineErrorCode(str, Enum):
    APPLICATION_NOT_FOUND = "APPLICATION_NOT_FOUND"
    OPPORTUNITY_NOT_FOUND = "OPPORTUNITY_NOT_FOUND"
    PROFILE_NOT_FOUND = "PROFILE_NOT_FOUND"
    DUPLICATE_APPLICATION = "DUPLICATE_APPLICATION"
    INVALID_STATUS_TRANSITION = "INVALID_STATUS_TRANSITION"
    INVALID_APPLICATION_STATE = "INVALID_APPLICATION_STATE"
    INTERVIEW_NOT_FOUND = "INTERVIEW_NOT_FOUND"
    REFERRAL_INVALID = "REFERRAL_INVALID"
    FOLLOW_UP_INVALID = "FOLLOW_UP_INVALID"
    APPLICATION_VALIDATION_ERROR = "APPLICATION_VALIDATION_ERROR"
    PIPELINE_INTERNAL_ERROR = "PIPELINE_INTERNAL_ERROR"


class PipelineException(Exception):
    """
    Domain exception for all Application Pipeline & Job Tracking operations.
    """

    def __init__(
        self,
        code: PipelineErrorCode,
        message: str,
        application_id: Optional[int] = None,
        opportunity_id: Optional[int] = None
    ):
        super().__init__(message)
        self.code = code
        self.message = message
        self.application_id = application_id
        self.opportunity_id = opportunity_id

