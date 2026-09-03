from enum import Enum
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from pydantic import BaseModel, Field


class ApplicationStatus(str, Enum):
    DISCOVERED = "DISCOVERED"
    SAVED = "SAVED"
    ASSETS_READY = "ASSETS_READY"
    READY_TO_APPLY = "READY_TO_APPLY"
    APPLIED = "APPLIED"
    INTERVIEWING = "INTERVIEWING"
    OFFER = "OFFER"
    REJECTED = "REJECTED"
    WITHDRAWN = "WITHDRAWN"
    CLOSED = "CLOSED"


class ApplicationPriority(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    URGENT = "URGENT"


class ReferralStatus(str, Enum):
    NOT_REQUESTED = "NOT_REQUESTED"
    REQUESTED = "REQUESTED"
    REFERRAL_PENDING = "REFERRAL_PENDING"
    REFERRED = "REFERRED"
    DECLINED = "DECLINED"
    NOT_AVAILABLE = "NOT_AVAILABLE"


class FollowUpStatus(str, Enum):
    NONE = "NONE"
    SCHEDULED = "SCHEDULED"
    DUE = "DUE"
    COMPLETED = "COMPLETED"
    OVERDUE = "OVERDUE"


class InterviewStage(str, Enum):
    SCREENING = "SCREENING"
    ONLINE_ASSESSMENT = "ONLINE_ASSESSMENT"
    TECHNICAL_ROUND = "TECHNICAL_ROUND"
    SYSTEM_DESIGN = "SYSTEM_DESIGN"
    HR_ROUND = "HR_ROUND"
    HIRING_MANAGER = "HIRING_MANAGER"
    FINAL_ROUND = "FINAL_ROUND"
    OTHER = "OTHER"


class InterviewMode(str, Enum):
    ONLINE = "ONLINE"
    PHONE = "PHONE"
    ONSITE = "ONSITE"
    VIDEO = "VIDEO"
    OTHER = "OTHER"


class InterviewStatus(str, Enum):
    SCHEDULED = "SCHEDULED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    RESCHEDULED = "RESCHEDULED"


class TimelineEventType(str, Enum):
    APPLICATION_CREATED = "APPLICATION_CREATED"
    STATUS_CHANGED = "STATUS_CHANGED"
    APPLICATION_MARKED_APPLIED = "APPLICATION_MARKED_APPLIED"
    REFERRAL_ADDED = "REFERRAL_ADDED"
    REFERRAL_STATUS_UPDATED = "REFERRAL_STATUS_UPDATED"
    FOLLOW_UP_SCHEDULED = "FOLLOW_UP_SCHEDULED"
    FOLLOW_UP_COMPLETED = "FOLLOW_UP_COMPLETED"
    INTERVIEW_SCHEDULED = "INTERVIEW_SCHEDULED"
    INTERVIEW_UPDATED = "INTERVIEW_UPDATED"
    OFFER_RECORDED = "OFFER_RECORDED"
    APPLICATION_REJECTED = "APPLICATION_REJECTED"
    APPLICATION_WITHDRAWN = "APPLICATION_WITHDRAWN"
    NOTE_ADDED = "NOTE_ADDED"


# -------------------------------------------------------------
# Request Schemas
# -------------------------------------------------------------

class CreateApplicationRequest(BaseModel):
    company: str = Field(..., min_length=1, max_length=255)
    role: str = Field(..., min_length=1, max_length=255)
    source_url: Optional[str] = None
    source_platform: Optional[str] = "manual"
    job_id: Optional[str] = None
    job_description: Optional[str] = None
    location: Optional[str] = None
    workplace_type: Optional[str] = None
    employment_type: Optional[str] = None
    priority: ApplicationPriority = ApplicationPriority.MEDIUM
    status: ApplicationStatus = ApplicationStatus.DISCOVERED
    match_score: Optional[int] = Field(default=None, ge=0, le=100)
    recommendation: Optional[str] = None
    notes: Optional[str] = None


class UpdateApplicationRequest(BaseModel):
    company: Optional[str] = Field(default=None, min_length=1, max_length=255)
    role: Optional[str] = Field(default=None, min_length=1, max_length=255)
    source_url: Optional[str] = None
    source_platform: Optional[str] = None
    job_id: Optional[str] = None
    job_description: Optional[str] = None
    location: Optional[str] = None
    workplace_type: Optional[str] = None
    employment_type: Optional[str] = None
    priority: Optional[ApplicationPriority] = None
    match_score: Optional[int] = Field(default=None, ge=0, le=100)
    recommendation: Optional[str] = None
    notes: Optional[str] = None


class ApplicationStatusTransitionRequest(BaseModel):
    status: ApplicationStatus
    note: Optional[str] = None


class MarkAppliedRequest(BaseModel):
    applied_at: Optional[datetime] = None
    note: Optional[str] = "Application marked as submitted manually."


class AddNoteRequest(BaseModel):
    note: str = Field(..., min_length=1)


class ReferralRequest(BaseModel):
    status: ReferralStatus = ReferralStatus.REQUESTED
    contact_name: Optional[str] = None
    contact_identifier: Optional[str] = None
    requested_date: Optional[datetime] = None
    referred_date: Optional[datetime] = None
    notes: Optional[str] = None


class FollowUpRequest(BaseModel):
    next_follow_up_date: datetime
    notes: Optional[str] = None


class InterviewCreateRequest(BaseModel):
    stage: InterviewStage
    scheduled_at: datetime
    duration_minutes: int = Field(default=60, ge=5, le=480)
    mode: InterviewMode = InterviewMode.ONLINE
    meeting_url: Optional[str] = None
    notes: Optional[str] = None


class InterviewUpdateRequest(BaseModel):
    stage: Optional[InterviewStage] = None
    scheduled_at: Optional[datetime] = None
    duration_minutes: Optional[int] = Field(default=None, ge=5, le=480)
    mode: Optional[InterviewMode] = None
    meeting_url: Optional[str] = None
    notes: Optional[str] = None
    status: Optional[InterviewStatus] = None


class ApplicationFilterParams(BaseModel):
    status: Optional[ApplicationStatus] = None
    company: Optional[str] = None
    role: Optional[str] = None
    priority: Optional[ApplicationPriority] = None
    referral_status: Optional[ReferralStatus] = None
    follow_up_status: Optional[FollowUpStatus] = None
    sort_by: str = Field(default="created_at", description="created_at, updated_at, match_score, priority, next_follow_up_date")
    sort_order: str = Field(default="desc", description="asc or desc")
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)


# -------------------------------------------------------------
# Response Schemas
# -------------------------------------------------------------

class ApplicationTimelineEventResponse(BaseModel):
    id: int
    application_id: int
    event_type: str
    timestamp: datetime
    description: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime

    class Config:
        from_attributes = True


class ApplicationStatusHistoryResponse(BaseModel):
    id: int
    application_id: int
    from_status: str
    to_status: str
    timestamp: datetime
    note: Optional[str] = None

    class Config:
        from_attributes = True


class InterviewResponse(BaseModel):
    id: int
    application_id: int
    stage: InterviewStage
    scheduled_at: datetime
    duration_minutes: int
    mode: InterviewMode
    meeting_url: Optional[str] = None
    notes: Optional[str] = None
    status: InterviewStatus
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ApplicationResponse(BaseModel):
    id: int
    profile_id: Optional[int] = None
    opportunity_id: Optional[int] = None
    company: str
    role: str
    source_url: Optional[str] = None
    source_platform: Optional[str] = None
    job_id: Optional[str] = None
    job_description: Optional[str] = None
    location: Optional[str] = None
    workplace_type: Optional[str] = None
    employment_type: Optional[str] = None
    status: ApplicationStatus
    priority: ApplicationPriority
    match_score: Optional[int] = None
    recommendation: Optional[str] = None
    date_discovered: Optional[datetime] = None
    date_saved: Optional[datetime] = None
    date_assets_generated: Optional[datetime] = None
    date_applied: Optional[datetime] = None
    last_status_update: Optional[datetime] = None
    next_follow_up_date: Optional[datetime] = None
    follow_up_status: FollowUpStatus
    referral_status: ReferralStatus
    referral_contact_name: Optional[str] = None
    referral_contact_identifier: Optional[str] = None
    referral_requested_date: Optional[datetime] = None
    referral_referred_date: Optional[datetime] = None
    referral_notes: Optional[str] = None
    interview_stage: Optional[str] = None
    interview_date: Optional[datetime] = None
    offer_date: Optional[datetime] = None
    rejection_date: Optional[datetime] = None
    withdrawal_date: Optional[datetime] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ApplicationListResponse(BaseModel):
    items: List[ApplicationResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class FollowUpCategoryResponse(BaseModel):
    scheduled: List[ApplicationResponse] = Field(default_factory=list)
    due: List[ApplicationResponse] = Field(default_factory=list)
    overdue: List[ApplicationResponse] = Field(default_factory=list)


class PipelineSummaryResponse(BaseModel):
    total_applications: int
    status_counts: Dict[str, int]
    priority_counts: Dict[str, int]
    applications_by_company: Dict[str, int]
    average_match_score: Optional[float] = None
    applied_count: int
    interview_count: int
    offer_count: int
    rejection_count: int
    follow_up_due_count: int
    follow_up_overdue_count: int
    referral_pending_count: int

