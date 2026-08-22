from enum import Enum
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class PipelineStatus(str, Enum):
    DISCOVERED = "DISCOVERED"
    SAVED = "SAVED"
    ANALYZED = "ANALYZED"
    ASSETS_GENERATED = "ASSETS_GENERATED"
    READY_TO_APPLY = "READY_TO_APPLY"
    APPLIED = "APPLIED"
    REJECTED = "REJECTED"
    ARCHIVED = "ARCHIVED"


class JobRecommendation(str, Enum):
    STRONG_MATCH = "STRONG_MATCH"
    GOOD_MATCH = "GOOD_MATCH"
    PARTIAL_MATCH = "PARTIAL_MATCH"
    WEAK_MATCH = "WEAK_MATCH"


class DiscoveredJob(BaseModel):
    id: Optional[int] = Field(default=None, description="Persistent opportunity database ID if saved")
    external_id: Optional[str] = Field(default=None, description="Unique identifier from job provider / ATS")
    provider: str = Field(..., description="Provider source name (greenhouse, lever, manual, etc.)")
    source_url: str = Field(..., description="Canonical URL of the job posting")
    application_url: Optional[str] = Field(default=None, description="Direct URL to application form if known")
    company: str = Field(..., description="Company name")
    title: str = Field(..., description="Job title / role name")
    location: Optional[str] = Field(default=None, description="Location text or Remote status")
    is_remote: Optional[bool] = Field(default=None, description="Whether the job is explicitly remote")
    description: str = Field(..., description="Cleaned job description text")
    employment_type: Optional[str] = Field(default=None, description="Full-time, Contract, etc.")
    experience_level: Optional[str] = Field(default=None, description="Senior, Mid, Entry, etc.")
    posted_at: Optional[str] = Field(default=None, description="Date or timestamp string when job was published")
    discovered_at: Optional[datetime] = Field(default_factory=datetime.utcnow, description="Timestamp of discovery")
    status: PipelineStatus = Field(default=PipelineStatus.DISCOVERED, description="Current opportunity pipeline state")
    
    # Candidate Matching & Ranking
    match_score: Optional[int] = Field(default=None, ge=0, le=100, description="Profile match score (0-100)")
    recommendation: Optional[JobRecommendation] = Field(default=None, description="Fit category")
    ranking_explanation: Optional[str] = Field(default=None, description="Reasoning behind match score and fit")
    matched_skills: List[str] = Field(default_factory=list, description="Demonstrated candidate skills matching the role")
    missing_skills: List[str] = Field(default_factory=list, description="Identified requirement gaps")
    key_strengths: List[str] = Field(default_factory=list, description="Primary candidate selling points for this role")
    key_concerns: List[str] = Field(default_factory=list, description="Primary missing criteria or potential risks")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Raw provider metadata")


class JobSearchQuery(BaseModel):
    keywords: List[str] = Field(default_factory=list, description="Keyword search terms (e.g. 'python', 'fastapi')")
    roles: List[str] = Field(default_factory=list, description="Target role titles (e.g. 'Backend Engineer')")
    locations: List[str] = Field(default_factory=list, description="Target locations or 'Remote'")
    companies: List[str] = Field(default_factory=list, description="Specific company slugs/boards to search (e.g. 'anthropic', 'figma')")
    remote_only: bool = Field(default=False, description="Filter only remote positions")
    employment_types: List[str] = Field(default_factory=list, description="e.g. ['full-time', 'contract']")
    experience_levels: List[str] = Field(default_factory=list, description="e.g. ['senior', 'mid']")
    providers: List[str] = Field(default_factory=list, description="Providers to query (defaults to all supported: greenhouse, lever)")
    max_results: int = Field(default=50, ge=1, le=200, description="Maximum number of discovered jobs to return")
    include_manual_urls: List[str] = Field(default_factory=list, description="Additional explicit job URLs to include and ingest")


class JobSearchResponse(BaseModel):
    success: bool
    total_discovered: int
    unique_opportunities: int
    duplicates_skipped: int
    opportunities: List[DiscoveredJob]
    warnings: List[str] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)


class ManualDiscoveryRequest(BaseModel):
    urls: List[str] = Field(..., min_length=1, description="List of job posting URLs to ingest and evaluate")


class ManualDiscoveryResponse(BaseModel):
    success: bool
    total_submitted: int
    unique_opportunities: int
    duplicates_skipped: int
    opportunities: List[DiscoveredJob]
    warnings: List[str] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)


class OpportunityFilterParams(BaseModel):
    min_match_score: Optional[int] = Field(default=None, ge=0, le=100)
    company: Optional[str] = None
    title: Optional[str] = None
    provider: Optional[str] = None
    location: Optional[str] = None
    is_remote: Optional[bool] = None
    status: Optional[PipelineStatus] = None
    sort_by: str = Field(default="match_score", description="match_score, newest, company, title")
    sort_order: str = Field(default="desc", description="asc or desc")
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)


class OpportunityListResponse(BaseModel):
    items: List[DiscoveredJob]
    total: int
    page: int
    page_size: int
    total_pages: int


class UpdateOpportunityStatusRequest(BaseModel):
    status: PipelineStatus = Field(..., description="Target pipeline lifecycle status")


class OpportunityActionResponse(BaseModel):
    success: bool
    opportunity_id: int
    status: PipelineStatus
    message: str
    data: Optional[Dict[str, Any]] = None
