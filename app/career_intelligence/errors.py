from enum import Enum
from typing import Optional


class CareerIntelligenceErrorCode(str, Enum):
    RECOMMENDATION_NOT_FOUND = "RECOMMENDATION_NOT_FOUND"
    APPLICATION_NOT_FOUND = "APPLICATION_NOT_FOUND"
    OPPORTUNITY_NOT_FOUND = "OPPORTUNITY_NOT_FOUND"
    INVALID_RECOMMENDATION_STATE = "INVALID_RECOMMENDATION_STATE"
    INVALID_PRIORITY = "INVALID_PRIORITY"
    INVALID_HEALTH_STATE = "INVALID_HEALTH_STATE"
    CAREER_INTELLIGENCE_VALIDATION_ERROR = "CAREER_INTELLIGENCE_VALIDATION_ERROR"
    CAREER_INTELLIGENCE_INTERNAL_ERROR = "CAREER_INTELLIGENCE_INTERNAL_ERROR"


class CareerIntelligenceException(Exception):
    """
    Domain exception for all Career Intelligence operations.
    """

    def __init__(
        self,
        code: CareerIntelligenceErrorCode,
        message: str,
        recommendation_id: Optional[int] = None,
        application_id: Optional[int] = None,
        opportunity_id: Optional[int] = None
    ):
        super().__init__(message)
        self.code = code
        self.message = message
        self.recommendation_id = recommendation_id
        self.application_id = application_id
        self.opportunity_id = opportunity_id

