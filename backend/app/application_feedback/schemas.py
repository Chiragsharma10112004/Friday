from datetime import datetime, timezone
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class OutcomeType(str, Enum):
    OFFER_RECEIVED = "OFFER_RECEIVED"
    OFFER_ACCEPTED = "OFFER_ACCEPTED"
    OFFER_DECLINED = "OFFER_DECLINED"
    REJECTED_AFTER_RESUME = "REJECTED_AFTER_RESUME"
    REJECTED_AFTER_SCREEN = "REJECTED_AFTER_SCREEN"
    REJECTED_AFTER_TECHNICAL = "REJECTED_AFTER_TECHNICAL"
    REJECTED_AFTER_FINAL = "REJECTED_AFTER_FINAL"
    WITHDRAWN = "WITHDRAWN"
    GHOSTED = "GHOSTED"


class FeedbackStage(str, Enum):
    RESUME_SCREEN = "RESUME_SCREEN"
    INITIAL_CALL = "INITIAL_CALL"
    TECHNICAL_ROUND = "TECHNICAL_ROUND"
    SYSTEM_DESIGN = "SYSTEM_DESIGN"
    TAKE_HOME = "TAKE_HOME"
    BEHAVIORAL = "BEHAVIORAL"
    FINAL_ROUND = "FINAL_ROUND"
    OFFER_STAGE = "OFFER_STAGE"


class DifficultyRating(str, Enum):
    VERY_EASY = "VERY_EASY"
    EASY = "EASY"
    MODERATE = "MODERATE"
    CHALLENGING = "CHALLENGING"
    VERY_CHALLENGING = "VERY_CHALLENGING"


class ExperienceRating(str, Enum):
    POSITIVE = "POSITIVE"
    NEUTRAL = "NEUTRAL"
    NEGATIVE = "NEGATIVE"


class FieldIssueType(str, Enum):
    UNRECOGNIZED_FIELD = "UNRECOGNIZED_FIELD"
    AUTOFIL_FAILED = "AUTOFIL_FAILED"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    CAPTCHA_TRIGGERED = "CAPTCHA_TRIGGERED"
    SESSION_TIMEOUT = "SESSION_TIMEOUT"
    FILE_UPLOAD_REQUIRED = "FILE_UPLOAD_REQUIRED"


class SignalType(str, Enum):
    SKILL_GAP_IDENTIFIED = "SKILL_GAP_IDENTIFIED"
    COMPANY_REJECTION_CLUSTER = "COMPANY_REJECTION_CLUSTER"
    HIGH_CONVERSION_RESUME = "HIGH_CONVERSION_RESUME"
    SLOW_RESPONSE_VELOCITY = "SLOW_RESPONSE_VELOCITY"
    INTERVIEW_PREPARATION_ALERT = "INTERVIEW_PREPARATION_ALERT"


# ==========================================
# OUTCOME FEEDBACK SCHEMAS
# ==========================================

class OutcomeFeedbackCreateRequest(BaseModel):
    application_id: int = Field(..., description="ID of the TrackedApplication")
    outcome_type: OutcomeType = Field(..., description="Categorized result of application/interview")
    feedback_stage: Optional[FeedbackStage] = Field(None, description="Stage at which outcome occurred")
    reasons_cited: Optional[List[str]] = Field(default_factory=list, description="Reasons cited for rejection or offer")
    skills_tested: Optional[List[str]] = Field(default_factory=list, description="Skills evaluated in interviews")
    skills_passed: Optional[List[str]] = Field(default_factory=list, description="Skills evaluated successfully")
    skills_failed: Optional[List[str]] = Field(default_factory=list, description="Skills evaluated with identified gaps")
    difficulty: Optional[DifficultyRating] = Field(None, description="Interview difficulty assessment")
    experience: Optional[ExperienceRating] = Field(None, description="Overall candidate candidate experience")
    salary_offered: Optional[float] = Field(None, description="Monetary compensation offered if applicable")
    interviewer_feedback: Optional[str] = Field(None, description="Sanitized summary notes from interviewer")
    notes: Optional[str] = Field(None, description="Candidate self-reflection or post-interview notes")


class OutcomeFeedbackResponse(BaseModel):
    id: int
    application_id: int
    profile_id: Optional[int] = None
    company: str
    role: str
    outcome_type: OutcomeType
    feedback_stage: Optional[FeedbackStage] = None
    reasons_cited: List[str] = Field(default_factory=list)
    skills_tested: List[str] = Field(default_factory=list)
    skills_passed: List[str] = Field(default_factory=list)
    skills_failed: List[str] = Field(default_factory=list)
    difficulty: Optional[DifficultyRating] = None
    experience: Optional[ExperienceRating] = None
    salary_offered: Optional[float] = None
    interviewer_feedback: Optional[str] = None
    notes: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


# ==========================================
# ASSET VERSIONING SCHEMAS
# ==========================================

class AssetVersionCreateRequest(BaseModel):
    application_id: int = Field(..., description="ID of the TrackedApplication")
    workflow_id: Optional[int] = Field(None, description="ID of the associated AutonomousWorkflow")
    resume_summary: Optional[str] = Field(None, description="Tailored professional summary used")
    resume_bullets: Optional[List[str]] = Field(default_factory=list, description="Tailored experience bullets used")
    cover_letter_text: Optional[str] = Field(None, description="Tailored cover letter text submitted")
    customizations_applied: Optional[List[str]] = Field(default_factory=list, description="Keywords/skills tailored")
    asset_score_at_application: Optional[int] = Field(None, description="Asset quality score at submission time")


class AssetVersionResponse(BaseModel):
    id: int
    application_id: int
    workflow_id: Optional[int] = None
    resume_summary: Optional[str] = None
    resume_bullets: List[str] = Field(default_factory=list)
    cover_letter_text: Optional[str] = None
    customizations_applied: List[str] = Field(default_factory=list)
    asset_score_at_application: Optional[int] = None
    created_at: Optional[datetime] = None


# ==========================================
# FIELD ISSUE SCHEMAS
# ==========================================

class FieldIssueCreateRequest(BaseModel):
    application_id: Optional[int] = Field(None, description="ID of associated TrackedApplication")
    workflow_id: Optional[int] = Field(None, description="ID of associated AutonomousWorkflow")
    platform: Optional[str] = Field("generic", description="Target ATS platform (e.g. greenhouse, lever)")
    field_name: str = Field(..., description="DOM field name or selector")
    field_label: Optional[str] = Field(None, description="Human-readable field label")
    field_type: Optional[str] = Field(None, description="HTML input type or control type")
    issue_type: FieldIssueType = Field(FieldIssueType.UNRECOGNIZED_FIELD, description="Classification of failure")
    error_message: Optional[str] = Field(None, description="Sanitized diagnostic error description")


class FieldIssueResponse(BaseModel):
    id: int
    application_id: Optional[int] = None
    workflow_id: Optional[int] = None
    platform: str
    field_name: str
    field_label: Optional[str] = None
    field_type: Optional[str] = None
    issue_type: FieldIssueType
    error_message: Optional[str] = None
    resolved: bool
    created_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None


# ==========================================
# FEEDBACK SIGNAL SCHEMAS
# ==========================================

class FeedbackSignalResponse(BaseModel):
    id: int
    signal_type: SignalType
    title: str
    description: str
    confidence_score: int
    affected_company: Optional[str] = None
    affected_skill: Optional[str] = None
    recommended_action: str
    created_at: Optional[datetime] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


# ==========================================
# ANALYTICS SCHEMAS
# ==========================================

class ConversionFunnelResponse(BaseModel):
    discovered: int
    saved: int
    applied: int
    screen: int
    technical: int
    final_round: int
    offers: int
    accepted: int
    rejected: int
    conversion_rates: Dict[str, float] = Field(default_factory=dict)


class PlatformPerformanceResponse(BaseModel):
    platform: str
    total_applications: int
    screen_rate: float
    offer_rate: float
    rejection_rate: float
    field_issue_count: int


class AssetPerformanceResponse(BaseModel):
    asset_version_id: Optional[int] = None
    customization_focus: str
    applications_count: int
    interviews_count: int
    offers_count: int
    interview_rate: float


class AnalyticsSummaryResponse(BaseModel):
    total_tracked: int
    total_applied: int
    total_interviews: int
    total_offers: int
    total_rejections: int
    overall_conversion_rate: float
    average_match_score_interviewed: float
    average_match_score_rejected: float
    funnel: ConversionFunnelResponse
    platform_metrics: List[PlatformPerformanceResponse] = Field(default_factory=list)
    active_signals_count: int


# ==========================================
# FEEDBACK RANKER SCHEMAS
# ==========================================

class FeedbackRankRequest(BaseModel):
    company: str = Field(..., description="Target company name")
    role: str = Field(..., description="Target role title")
    match_score: int = Field(..., ge=0, le=100, description="Baseline profile match score (0-100)")
    missing_skills: Optional[List[str]] = Field(default_factory=list, description="Skill gaps identified for job")
    platform: Optional[str] = Field("generic", description="Target job platform")


class FeedbackRankResponse(BaseModel):
    base_score: int
    adjusted_score: int
    priority: str
    recommendation: str
    feedback_adjustments: List[str] = Field(default_factory=list)
    risk_flags: List[str] = Field(default_factory=list)
