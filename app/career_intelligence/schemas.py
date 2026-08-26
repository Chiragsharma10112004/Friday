from enum import Enum
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class RecommendationType(str, Enum):
    APPLY_NOW = "APPLY_NOW"
    PRIORITY_APPLICATION = "PRIORITY_APPLICATION"
    GENERATE_ASSETS = "GENERATE_ASSETS"
    REQUEST_REFERRAL = "REQUEST_REFERRAL"
    FOLLOW_UP_DUE = "FOLLOW_UP_DUE"
    FOLLOW_UP_OVERDUE = "FOLLOW_UP_OVERDUE"
    INTERVIEW_PREPARATION = "INTERVIEW_PREPARATION"
    STALE_APPLICATION = "STALE_APPLICATION"
    APPLICATION_STATUS_REVIEW = "APPLICATION_STATUS_REVIEW"
    UPDATE_APPLICATION = "UPDATE_APPLICATION"
    CLOSE_INACTIVE_APPLICATION = "CLOSE_INACTIVE_APPLICATION"


class RecommendationStatus(str, Enum):
    ACTIVE = "ACTIVE"
    DISMISSED = "DISMISSED"
    COMPLETED = "COMPLETED"
    EXPIRED = "EXPIRED"


class ActionPriority(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    URGENT = "URGENT"


class HealthCategory(str, Enum):
    EXCELLENT = "EXCELLENT"
    HEALTHY = "HEALTHY"
    ATTENTION_NEEDED = "ATTENTION_NEEDED"
    STALE = "STALE"
    CRITICAL = "CRITICAL"


# -------------------------------------------------------------
# Scoring and Health Engine Models
# -------------------------------------------------------------

class PriorityScoreResult(BaseModel):
    total_score: int = Field(ge=0, le=100)
    breakdown: Dict[str, int]
    reasoning: List[str]


class ApplicationHealthResult(BaseModel):
    health: HealthCategory
    score: int = Field(ge=0, le=100)
    reasons: List[str]
    recommended_action: str


# -------------------------------------------------------------
# Action & Recommendation Schemas
# -------------------------------------------------------------

class ActionItemResponse(BaseModel):
    id: Optional[int] = None
    type: RecommendationType
    priority: ActionPriority
    title: str
    description: str
    reason: str
    recommended_action: str
    score: Optional[int] = None
    application_id: Optional[int] = None
    opportunity_id: Optional[int] = None
    status: RecommendationStatus = RecommendationStatus.ACTIVE
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        from_attributes = True


class TodayActionQueueResponse(BaseModel):
    success: bool = True
    date: str
    summary: str
    action_count: int
    urgent_count: int
    high_priority_count: int
    actions: List[ActionItemResponse]


class ApplicationHealthItem(BaseModel):
    application_id: int
    company: str
    role: str
    status: str
    health: HealthCategory
    health_score: int
    priority_score: int
    reasons: List[str]
    recommended_action: str
    last_status_update: Optional[datetime] = None
    next_follow_up_date: Optional[datetime] = None


class ApplicationHealthListResponse(BaseModel):
    total: int
    items: List[ApplicationHealthItem]


class DashboardIntelligenceResponse(BaseModel):
    total_active_applications: int
    healthy_applications: int
    attention_needed: int
    stale: int
    critical: int
    urgent_actions: int
    high_priority_actions: int
    overdue_follow_ups: int
    upcoming_interviews: int
    pending_referrals: int
    average_application_health: float
    top_priority_applications: List[Dict[str, Any]]


class DailyBriefingResponse(BaseModel):
    date: str
    summary: str
    applications_requiring_action: int
    overdue_follow_ups: int
    due_today: int
    upcoming_interviews: int
    pending_referrals: int
    stale_applications: int
    top_priority_applications: List[Dict[str, Any]]
    top_opportunities: List[Dict[str, Any]]
    recommended_next_actions: List[ActionItemResponse]


class WeeklyBriefingResponse(BaseModel):
    date: str
    total_applications: int
    applications_created_this_week: int
    applications_applied_this_week: int
    applications_currently_interviewing: int
    new_offers: int
    rejections: int
    withdrawals: int
    follow_ups_completed: int
    overdue_follow_ups: int
    average_match_score: Optional[float] = None
    top_companies: Dict[str, int]
    status_distribution: Dict[str, int]
    priority_distribution: Dict[str, int]
    referral_distribution: Dict[str, int]
    recommended_focus_next_week: List[str]


class RefreshResponse(BaseModel):
    success: bool = True
    created_count: int
    updated_count: int
    expired_count: int
    active_count: int

