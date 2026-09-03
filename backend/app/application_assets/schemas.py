from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

from app.ingestion.schemas import NormalizedJobPosting


class AssetType(str, Enum):
    RESUME = "resume"
    COVER_LETTER = "cover_letter"
    RECRUITER_MESSAGE = "recruiter_message"
    SKILL_GAP = "skill_gap"
    APPLICATION_SUMMARY = "application_summary"


class CoverLetterStyle(str, Enum):
    CONCISE = "concise"
    STANDARD = "standard"
    DETAILED = "detailed"


class MessageChannel(str, Enum):
    LINKEDIN = "linkedin"
    EMAIL = "email"
    DIRECT_MESSAGE = "direct_message"


class MessageTone(str, Enum):
    PROFESSIONAL = "professional"
    FRIENDLY = "friendly"
    CONCISE = "concise"


class ClaimEvidenceType(str, Enum):
    VERIFIED_CANDIDATE_FACT = "VERIFIED_CANDIDATE_FACT"
    REWRITE_OF_CANDIDATE_FACT = "REWRITE_OF_CANDIDATE_FACT"
    SUGGESTED_POSITIONING = "SUGGESTED_POSITIONING"


class EvidenceMetadata(BaseModel):
    claim: str
    claim_type: ClaimEvidenceType
    source_field: Optional[str] = None  # e.g., 'skills', 'projects', 'experience', 'education'
    confidence: str = "high"


class TailoredProjectAsset(BaseModel):
    name: str
    description: str
    bullet_points: List[str] = Field(default_factory=list)
    matched_skills: List[str] = Field(default_factory=list)


class TailoredResumeAsset(BaseModel):
    professional_summary: str
    relevant_skills: List[str] = Field(default_factory=list)
    relevant_projects: List[TailoredProjectAsset] = Field(default_factory=list)
    experience_bullets: List[str] = Field(default_factory=list)
    achievement_bullets: List[str] = Field(default_factory=list)
    keywords_matched: List[str] = Field(default_factory=list)
    keywords_missing: List[str] = Field(default_factory=list)
    sections_to_prioritize: List[str] = Field(default_factory=list)


class CoverLetterAsset(BaseModel):
    letter_text: str
    style: CoverLetterStyle = CoverLetterStyle.STANDARD
    key_highlights: List[str] = Field(default_factory=list)
    evidence_used: List[str] = Field(default_factory=list)


class RecruiterMessageAsset(BaseModel):
    message_text: str
    channel: MessageChannel = MessageChannel.LINKEDIN
    tone: MessageTone = MessageTone.PROFESSIONAL
    character_count: int = 0


class PriorityGap(BaseModel):
    skill: str
    priority: str = "MEDIUM"  # HIGH, MEDIUM, LOW
    reason: str
    evidence_from_jd: str
    suggested_action: str


class SkillGapAnalysis(BaseModel):
    matched_skills: List[str] = Field(default_factory=list)
    partially_matched_skills: List[str] = Field(default_factory=list)
    missing_skills: List[str] = Field(default_factory=list)
    transferable_skills: List[str] = Field(default_factory=list)
    priority_gaps: List[PriorityGap] = Field(default_factory=list)
    recommended_learning_actions: List[str] = Field(default_factory=list)


class ApplicationSummaryAsset(BaseModel):
    overall_fit: str  # STRONG_MATCH, MODERATE_MATCH, WEAK_MATCH, SKIP
    strongest_selling_points: List[str] = Field(default_factory=list)
    biggest_concerns: List[str] = Field(default_factory=list)
    missing_requirements: List[str] = Field(default_factory=list)
    recommended_assets: List[str] = Field(default_factory=list)
    apply_recommendation: str  # APPLY, MAYBE, SKIP


class GeneratedAssetsBundle(BaseModel):
    resume: Optional[TailoredResumeAsset] = None
    cover_letter: Optional[CoverLetterAsset] = None
    recruiter_message: Optional[RecruiterMessageAsset] = None
    skill_gap: Optional[SkillGapAnalysis] = None
    application_summary: Optional[ApplicationSummaryAsset] = None


class ApplicationAssetRequest(BaseModel):
    # Input Modalities: raw text, normalized posting, or existing application ID
    job_description: Optional[str] = Field(default=None, description="Raw job description text")
    company: Optional[str] = Field(default=None, description="Hiring company name")
    role: Optional[str] = Field(default=None, description="Role / title")
    application_id: Optional[int] = Field(default=None, description="Existing JobApplication database ID")
    normalized_job: Optional[NormalizedJobPosting] = Field(default=None, description="Ingested job posting from Phase 2")

    # Selection & Style Preferences
    assets: List[AssetType] = Field(
        default_factory=lambda: [
            AssetType.RESUME,
            AssetType.COVER_LETTER,
            AssetType.RECRUITER_MESSAGE,
            AssetType.SKILL_GAP,
            AssetType.APPLICATION_SUMMARY,
        ],
        description="List of assets to generate"
    )
    cover_letter_style: CoverLetterStyle = CoverLetterStyle.STANDARD
    message_style: MessageChannel = MessageChannel.LINKEDIN
    message_tone: MessageTone = MessageTone.PROFESSIONAL


class ApplicationAssetResponse(BaseModel):
    success: bool
    company: str
    role: str
    match_score: int
    recommendation: str
    assets: GeneratedAssetsBundle
    evidence_metadata: List[EvidenceMetadata] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)

