from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

from app.ingestion.schemas import NormalizedJobPosting


class FormPlatform(str, Enum):
    GREENHOUSE = "greenhouse"
    LEVER = "lever"
    WORKDAY = "workday"
    LINKEDIN = "linkedin"
    INDEED = "indeed"
    GENERIC = "generic"
    UNSUPPORTED = "unsupported"


class FieldConfidence(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    UNSUPPORTED = "UNSUPPORTED"


class FieldStatus(str, Enum):
    AUTO_FILL_READY = "AUTO_FILL_READY"
    APPROVAL_REQUIRED = "APPROVAL_REQUIRED"
    MANUAL_REQUIRED = "MANUAL_REQUIRED"
    UNSUPPORTED = "UNSUPPORTED"


class QuestionType(str, Enum):
    TEXT = "text"
    EMAIL = "email"
    TEL = "tel"
    TEXTAREA = "textarea"
    SELECT = "select"
    RADIO = "radio"
    CHECKBOX = "checkbox"
    DATE = "date"
    FILE = "file"
    UNKNOWN = "unknown"


class InspectionStatus(str, Enum):
    PREVIEW_READY = "PREVIEW_READY"
    CAPTCHA_DETECTED = "CAPTCHA_DETECTED"
    AUTHENTICATION_REQUIRED = "AUTHENTICATION_REQUIRED"
    ACCESS_RESTRICTED = "ACCESS_RESTRICTED"
    FAILED = "FAILED"


class FieldInspectionItem(BaseModel):
    field_id: str = Field(..., description="Unique CSS selector or DOM identifier for the form control")
    label: str = Field(..., description="Visible human-readable question or label text")
    html_name: Optional[str] = Field(default=None, description="HTML name or id attribute")
    control_type: QuestionType = Field(default=QuestionType.TEXT, description="Detected HTML control type")
    normalized_field: Optional[str] = Field(default=None, description="Canonical mapping key (e.g. first_name, email)")
    suggested_value: Optional[str] = Field(default=None, description="Candidate fact suggested for filling")
    source: Optional[str] = Field(default=None, description="Origin of suggested value (e.g. profile.first_name)")
    confidence: FieldConfidence = Field(default=FieldConfidence.LOW, description="Mapping confidence score")
    status: FieldStatus = Field(default=FieldStatus.MANUAL_REQUIRED, description="Automation review category")
    requires_approval: bool = Field(default=True, description="True if human confirmation is required before filling")
    options: List[str] = Field(default_factory=list, description="Available choices for select/radio/checkbox controls")
    is_sensitive: bool = Field(default=False, description="True for legal, demographic, or salary questions")
    validation_notice: Optional[str] = Field(default=None, description="Advisory explanation or manual guidance")


class InspectApplicationRequest(BaseModel):
    application_url: Optional[str] = Field(default=None, description="Target job application form URL")
    application_id: Optional[int] = Field(default=None, description="Database JobApplication ID")
    normalized_job: Optional[NormalizedJobPosting] = Field(default=None, description="Phase 2 Ingested Job Posting")


class InspectApplicationResponse(BaseModel):
    success: bool
    session_id: str = Field(..., description="Inspection session token for Stage B filling")
    platform: FormPlatform = Field(default=FormPlatform.GENERIC)
    status: InspectionStatus = Field(default=InspectionStatus.PREVIEW_READY)
    page_url: str
    page_title: Optional[str] = None
    fields: List[FieldInspectionItem] = Field(default_factory=list)
    auto_fill_ready_count: int = 0
    approval_required_count: int = 0
    manual_required_count: int = 0
    unsupported_count: int = 0
    warnings: List[str] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)
    submission_allowed: bool = Field(default=False, description="Hard safety invariant: always False")


class FillApprovedFieldsRequest(BaseModel):
    session_id: str = Field(..., description="Active inspection session token")
    approved_field_ids: List[str] = Field(default_factory=list, description="List of field IDs explicitly approved for filling")
    custom_answers: Dict[str, str] = Field(default_factory=dict, description="User-supplied overrides or answers for manual questions")


class FieldFillResult(BaseModel):
    field_id: str
    label: str
    normalized_field: Optional[str] = None
    value_filled: str
    success: bool
    notice: Optional[str] = None


class FillApprovedFieldsResponse(BaseModel):
    success: bool
    session_id: str
    platform: FormPlatform
    fields_filled: List[FieldFillResult] = Field(default_factory=list)
    fields_skipped: List[str] = Field(default_factory=list)
    manual_fields_remaining: List[str] = Field(default_factory=list)
    submission_performed: bool = Field(default=False, description="Hard safety invariant: always False")
    manual_submission_required: bool = Field(default=True, description="Human user must review and manually submit")
    warnings: List[str] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)

