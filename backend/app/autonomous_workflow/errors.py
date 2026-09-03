from enum import Enum
from typing import Optional


class WorkflowErrorCode(str, Enum):
    WORKFLOW_NOT_FOUND = "WORKFLOW_NOT_FOUND"
    DUPLICATE_WORKFLOW = "DUPLICATE_WORKFLOW"
    INVALID_WORKFLOW_TRANSITION = "INVALID_WORKFLOW_TRANSITION"
    WORKFLOW_NOT_STARTABLE = "WORKFLOW_NOT_STARTABLE"
    WORKFLOW_PAUSED = "WORKFLOW_PAUSED"
    WORKFLOW_NOT_PAUSED = "WORKFLOW_NOT_PAUSED"
    WORKFLOW_CANCELLED = "WORKFLOW_CANCELLED"
    WORKFLOW_ALREADY_COMPLETED = "WORKFLOW_ALREADY_COMPLETED"
    APPROVAL_NOT_FOUND = "APPROVAL_NOT_FOUND"
    APPROVAL_REQUIRED = "APPROVAL_REQUIRED"
    APPROVAL_REJECTED = "APPROVAL_REJECTED"
    USER_ACTION_REQUIRED = "USER_ACTION_REQUIRED"
    RETRY_NOT_ALLOWED = "RETRY_NOT_ALLOWED"
    RETRY_LIMIT_REACHED = "RETRY_LIMIT_REACHED"
    APPLICATION_NOT_FOUND = "APPLICATION_NOT_FOUND"
    OPPORTUNITY_NOT_FOUND = "OPPORTUNITY_NOT_FOUND"
    ASSET_GENERATION_FAILED = "ASSET_GENERATION_FAILED"
    APPLICATION_INSPECTION_FAILED = "APPLICATION_INSPECTION_FAILED"
    AUTOFILL_FAILED = "AUTOFILL_FAILED"
    MANUAL_SUBMISSION_REQUIRED = "MANUAL_SUBMISSION_REQUIRED"
    DISCOVERY_FAILED = "DISCOVERY_FAILED"
    WORKFLOW_VALIDATION_ERROR = "WORKFLOW_VALIDATION_ERROR"
    WORKFLOW_INTERNAL_ERROR = "WORKFLOW_INTERNAL_ERROR"


class WorkflowException(Exception):
    """
    Domain exception for all autonomous workflow operations.
    """

    def __init__(
        self,
        code: WorkflowErrorCode,
        message: str,
        workflow_id: Optional[int] = None,
        step_id: Optional[int] = None,
        approval_id: Optional[int] = None,
        details: Optional[dict] = None,
    ):
        super().__init__(message)
        self.code = code
        self.message = message
        self.workflow_id = workflow_id
        self.step_id = step_id
        self.approval_id = approval_id
        self.details = details or {}
