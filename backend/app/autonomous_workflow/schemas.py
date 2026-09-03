from enum import Enum
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


# -------------------------------------------------------------
# Enums
# -------------------------------------------------------------

class WorkflowStatus(str, Enum):
    CREATED = "CREATED"
    DISCOVERED = "DISCOVERED"
    ANALYZING = "ANALYZING"
    ANALYZED = "ANALYZED"
    SCORED = "SCORED"
    QUEUED_FOR_REVIEW = "QUEUED_FOR_REVIEW"
    AWAITING_APPROVAL = "AWAITING_APPROVAL"
    APPROVED = "APPROVED"
    PLANNING = "PLANNING"
    ASSETS_GENERATING = "ASSETS_GENERATING"
    ASSETS_READY = "ASSETS_READY"
    APPLICATION_INSPECTING = "APPLICATION_INSPECTING"
    APPLICATION_INSPECTED = "APPLICATION_INSPECTED"
    AUTOFILL_READY = "AUTOFILL_READY"
    AUTOFILLING = "AUTOFILLING"
    AWAITING_USER_ACTION = "AWAITING_USER_ACTION"
    AWAITING_MANUAL_REVIEW = "AWAITING_MANUAL_REVIEW"
    READY_FOR_FINAL_REVIEW = "READY_FOR_FINAL_REVIEW"
    SUBMISSION_PENDING = "SUBMISSION_PENDING"
    APPLICATION_COMPLETED = "APPLICATION_COMPLETED"
    PAUSED = "PAUSED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    CLOSED = "CLOSED"


class WorkflowPriority(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    URGENT = "URGENT"


class WorkflowStepStatus(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    WAITING = "WAITING"
    SKIPPED = "SKIPPED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class ApprovalType(str, Enum):
    APPLICATION_APPROVAL = "APPLICATION_APPROVAL"
    ASSET_APPROVAL = "ASSET_APPROVAL"
    AUTOFILL_APPROVAL = "AUTOFILL_APPROVAL"
    REFERRAL_APPROVAL = "REFERRAL_APPROVAL"
    MANUAL_CHECKPOINT_ACKNOWLEDGEMENT = "MANUAL_CHECKPOINT_ACKNOWLEDGEMENT"
    RESUME_WORKFLOW = "RESUME_WORKFLOW"


class ApprovalStatus(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"
    CANCELLED = "CANCELLED"


class UserActionType(str, Enum):
    NONE = "NONE"
    APPROVE_APPLICATION = "APPROVE_APPLICATION"
    CREATE_ACCOUNT = "CREATE_ACCOUNT"
    SIGN_IN = "SIGN_IN"
    ENTER_PASSWORD = "ENTER_PASSWORD"
    VERIFY_EMAIL = "VERIFY_EMAIL"
    ENTER_OTP = "ENTER_OTP"
    SOLVE_CAPTCHA = "SOLVE_CAPTCHA"
    ANSWER_SENSITIVE_QUESTION = "ANSWER_SENSITIVE_QUESTION"
    REVIEW_AUTOFILL = "REVIEW_AUTOFILL"
    SUBMIT_APPLICATION_MANUALLY = "SUBMIT_APPLICATION_MANUALLY"
    CONFIRM_APPLICATION_SUBMITTED = "CONFIRM_APPLICATION_SUBMITTED"
    REQUEST_REFERRAL = "REQUEST_REFERRAL"
    COMPLETE_REFERRAL_STEP = "COMPLETE_REFERRAL_STEP"
    OTHER = "OTHER"


class PauseReason(str, Enum):
    USER_ACTION_REQUIRED = "USER_ACTION_REQUIRED"
    APPROVAL_REQUIRED = "APPROVAL_REQUIRED"
    AUTHENTICATION_REQUIRED = "AUTHENTICATION_REQUIRED"
    ACCOUNT_CREATION_REQUIRED = "ACCOUNT_CREATION_REQUIRED"
    EMAIL_VERIFICATION_REQUIRED = "EMAIL_VERIFICATION_REQUIRED"
    CAPTCHA_DETECTED = "CAPTCHA_DETECTED"
    SENSITIVE_FIELD_REQUIRED = "SENSITIVE_FIELD_REQUIRED"
    MANUAL_REVIEW_REQUIRED = "MANUAL_REVIEW_REQUIRED"
    NETWORK_ERROR = "NETWORK_ERROR"
    RETRY_LIMIT_REACHED = "RETRY_LIMIT_REACHED"
    EXTERNAL_SERVICE_FAILURE = "EXTERNAL_SERVICE_FAILURE"
    USER_PAUSED = "USER_PAUSED"


class WorkflowActionType(str, Enum):
    WORKFLOW_CREATED = "WORKFLOW_CREATED"
    OPPORTUNITY_LINKED = "OPPORTUNITY_LINKED"
    JOB_ANALYSIS_STARTED = "JOB_ANALYSIS_STARTED"
    JOB_ANALYSIS_COMPLETED = "JOB_ANALYSIS_COMPLETED"
    JOB_SCORED = "JOB_SCORED"
    APPLICATION_CREATED = "APPLICATION_CREATED"
    APPLICATION_APPROVAL_REQUESTED = "APPLICATION_APPROVAL_REQUESTED"
    APPLICATION_APPROVED = "APPLICATION_APPROVED"
    APPLICATION_REJECTED = "APPLICATION_REJECTED"
    ASSET_GENERATION_STARTED = "ASSET_GENERATION_STARTED"
    ASSET_GENERATION_COMPLETED = "ASSET_GENERATION_COMPLETED"
    APPLICATION_INSPECTION_STARTED = "APPLICATION_INSPECTION_STARTED"
    APPLICATION_INSPECTION_COMPLETED = "APPLICATION_INSPECTION_COMPLETED"
    AUTOFILL_APPROVAL_REQUESTED = "AUTOFILL_APPROVAL_REQUESTED"
    AUTOFILL_STARTED = "AUTOFILL_STARTED"
    AUTOFILL_COMPLETED = "AUTOFILL_COMPLETED"
    WORKFLOW_PAUSED = "WORKFLOW_PAUSED"
    WORKFLOW_RESUMED = "WORKFLOW_RESUMED"
    USER_ACTION_REQUIRED = "USER_ACTION_REQUIRED"
    REFERRAL_RECOMMENDED = "REFERRAL_RECOMMENDED"
    REFERRAL_REQUESTED = "REFERRAL_REQUESTED"
    RETRY_SCHEDULED = "RETRY_SCHEDULED"
    RETRY_ATTEMPTED = "RETRY_ATTEMPTED"
    WORKFLOW_FAILED = "WORKFLOW_FAILED"
    WORKFLOW_COMPLETED = "WORKFLOW_COMPLETED"
    APPLICATION_MARKED_MANUALLY_SUBMITTED = "APPLICATION_MARKED_MANUALLY_SUBMITTED"


# -------------------------------------------------------------
# Request & Response Models
# -------------------------------------------------------------

class WorkflowCreateRequest(BaseModel):
    company: str
    role: str
    source_url: Optional[str] = None
    source_platform: Optional[str] = None
    priority: WorkflowPriority = WorkflowPriority.MEDIUM
    opportunity_id: Optional[int] = None
    application_id: Optional[int] = None
    job_description: Optional[str] = None
    match_score: Optional[int] = None


class WorkflowFromOpportunityRequest(BaseModel):
    opportunity_id: int
    priority: Optional[WorkflowPriority] = None


class WorkflowStepResponse(BaseModel):
    id: int
    workflow_id: int
    step_name: str
    step_order: int
    status: WorkflowStepStatus
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    retry_count: int = 0
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class WorkflowStepListResponse(BaseModel):
    total: int
    steps: List[WorkflowStepResponse]


class WorkflowApprovalResponse(BaseModel):
    id: int
    workflow_id: int
    approval_type: ApprovalType
    status: ApprovalStatus
    requested_at: Optional[datetime] = None
    approved_at: Optional[datetime] = None
    rejected_at: Optional[datetime] = None
    approved_by: Optional[str] = None
    reason: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class WorkflowApprovalListResponse(BaseModel):
    total: int
    approvals: List[WorkflowApprovalResponse]


class WorkflowApproveRequest(BaseModel):
    approval_type: Optional[ApprovalType] = None
    approved_by: str = "user"
    reason: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class WorkflowRejectRequest(BaseModel):
    approval_type: Optional[ApprovalType] = None
    rejected_by: str = "user"
    reason: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class WorkflowActionLogResponse(BaseModel):
    id: int
    workflow_id: int
    action_type: WorkflowActionType
    description: str
    status: str
    timestamp: Optional[datetime] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        from_attributes = True


class WorkflowActionLogListResponse(BaseModel):
    total: int
    logs: List[WorkflowActionLogResponse]


class WorkflowResponse(BaseModel):
    id: int
    profile_id: Optional[int] = None
    application_id: Optional[int] = None
    opportunity_id: Optional[int] = None
    company: str
    role: str
    source_url: Optional[str] = None
    source_platform: Optional[str] = None
    workflow_status: WorkflowStatus
    workflow_priority: WorkflowPriority
    match_score: Optional[int] = None
    recommendation_score: Optional[int] = None
    current_step: Optional[str] = None
    next_action: Optional[str] = None
    approval_required: bool = False
    user_action_required: bool = False
    paused: bool = False
    pause_reason: Optional[str] = None
    retry_count: int = 0
    last_error: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    paused_at: Optional[datetime] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        from_attributes = True


class WorkflowListResponse(BaseModel):
    total: int
    items: List[WorkflowResponse]


class WorkflowPlanStep(BaseModel):
    step: str
    required: bool = True
    approval_required: bool = False
    recommended: Optional[bool] = None
    automation_allowed: bool = True
    description: Optional[str] = None


class WorkflowPlanResponse(BaseModel):
    workflow_id: int
    company: str
    role: str
    plan: List[WorkflowPlanStep]


class WorkflowNextActionResponse(BaseModel):
    workflow_id: int
    status: WorkflowStatus
    current_step: Optional[str] = None
    next_action: str
    user_action_required: bool
    action_type: UserActionType
    instructions: str
    manual_submission_required: bool = True


class WorkflowQueueItem(BaseModel):
    workflow_id: int
    application_id: Optional[int] = None
    opportunity_id: Optional[int] = None
    company: str
    role: str
    match_score: Optional[int] = None
    priority: WorkflowPriority
    workflow_status: WorkflowStatus
    current_step: Optional[str] = None
    next_action: Optional[str] = None
    pause_reason: Optional[str] = None
    user_action_required: bool
    action_type: Optional[UserActionType] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class WorkflowQueueResponse(BaseModel):
    total: int
    urgent: List[WorkflowQueueItem]
    high_priority: List[WorkflowQueueItem]
    ready_for_approval: List[WorkflowQueueItem]
    ready_for_assets: List[WorkflowQueueItem]
    ready_for_autofill: List[WorkflowQueueItem]
    awaiting_user_action: List[WorkflowQueueItem]
    awaiting_manual_review: List[WorkflowQueueItem]
    ready_for_submission: List[WorkflowQueueItem]
    paused: List[WorkflowQueueItem]
    failed: List[WorkflowQueueItem]
    completed: List[WorkflowQueueItem]


class WorkflowDashboardResponse(BaseModel):
    total_active_workflows: int
    awaiting_approval: int
    awaiting_user_action: int
    ready_for_submission: int
    paused: int
    failed: int
    completed: int
    high_priority_count: int
    urgent_count: int
    average_match_score: Optional[float] = None
    top_companies: Dict[str, int]
    recent_activity: List[WorkflowActionLogResponse]
    upcoming_follow_ups: int
    referral_pending_count: int
    application_status_distribution: Dict[str, int]


class DiscoveryRunResponse(BaseModel):
    success: bool = True
    opportunities_discovered: int
    workflows_created: int
    workflows_queued: int
    min_score_threshold: int


class ReferralUpdateRequest(BaseModel):
    referral_contact_name: Optional[str] = None
    referral_contact_identifier: Optional[str] = None
    referral_notes: Optional[str] = None
    referral_status: Optional[str] = None
