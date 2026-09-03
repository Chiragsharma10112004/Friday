from enum import Enum
from typing import Optional, Dict, Any


class SelfHealingErrorCode(str, Enum):
    DIAGNOSTIC_FAILED = "DIAGNOSTIC_FAILED"
    PLANNING_FAILED = "PLANNING_FAILED"
    VALIDATION_FAILED = "VALIDATION_FAILED"
    ROLLBACK_FAILED = "ROLLBACK_FAILED"
    APPROVAL_REQUIRED = "APPROVAL_REQUIRED"
    TARGET_NOT_FOUND = "TARGET_NOT_FOUND"
    EXECUTION_ERROR = "EXECUTION_ERROR"
    MAX_RETRIES_EXCEEDED = "MAX_RETRIES_EXCEEDED"


class SelfHealingException(Exception):
    """Domain exception for Phase 9 Self-Healing operations."""

    def __init__(
        self,
        code: SelfHealingErrorCode,
        message: str,
        details: Optional[Dict[str, Any]] = None
    ):
        self.code = code
        self.message = message
        self.details = details or {}
        super().__init__(self.message)
