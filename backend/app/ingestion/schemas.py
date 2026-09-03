from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

from app.ingestion.errors import IngestionErrorCode


class IngestJobRequest(BaseModel):
    job_url: str = Field(
        ...,
        min_length=5,
        description="Public URL of the job posting"
    )


class NormalizedJobPosting(BaseModel):
    # Core Required Data
    company: str = Field(..., description="Name of the hiring company")
    role: str = Field(..., description="Job title / role name")
    job_description: str = Field(..., description="Cleaned, full job description text")
    source_platform: str = Field(..., description="Platform name (greenhouse, lever, generic, etc.)")
    source_url: str = Field(..., description="Canonical source URL")

    # Optional Structured Fields
    location: Optional[str] = Field(default=None, description="Job location or Remote status")
    employment_type: Optional[str] = Field(default=None, description="Full-time, Part-time, Contract, Internship, etc.")
    salary_range: Optional[str] = Field(default=None, description="Compensation / salary range if disclosed")
    department: Optional[str] = Field(default=None, description="Team, department, or business unit")
    workplace_type: Optional[str] = Field(default=None, description="Remote, Hybrid, On-site")
    experience_level: Optional[str] = Field(default=None, description="Senior, Mid, Entry-level, etc.")
    posted_date: Optional[str] = Field(default=None, description="Date job was published/updated")
    job_id: Optional[str] = Field(default=None, description="Internal requisition or job ID")

    # Detailed Structured Content
    requirements: List[str] = Field(default_factory=list, description="Extracted qualifications or requirements")
    responsibilities: List[str] = Field(default_factory=list, description="Extracted core job responsibilities")
    benefits: List[str] = Field(default_factory=list, description="Extracted benefits or perks")

    # Metadata & Confidence
    confidence: str = Field(default="high", description="Extraction confidence: high, medium, low")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Raw source metadata or extra attributes")


class IngestionError(BaseModel):
    code: IngestionErrorCode
    message: str
    retryable: bool = False


class IngestionWarning(BaseModel):
    code: str
    message: str


class IngestJobResponse(BaseModel):
    success: bool
    source_platform: Optional[str] = None
    data: Optional[NormalizedJobPosting] = None
    warnings: List[IngestionWarning] = Field(default_factory=list)
    errors: List[IngestionError] = Field(default_factory=list)

