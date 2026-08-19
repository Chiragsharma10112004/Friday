from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class JobApplicationCreate(BaseModel):
    company: str = Field(
        ...,
        min_length=1,
        max_length=255
    )

    role: str = Field(
        ...,
        min_length=1,
        max_length=255
    )

    job_url: Optional[str] = None
    job_description: Optional[str] = None

    match_score: Optional[int] = Field(
        default=None,
        ge=0,
        le=100
    )

    recommendation: Optional[str] = None

    status: str = "NOT_APPLIED"


class JobApplicationUpdate(BaseModel):
    company: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=255
    )

    role: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=255
    )

    job_url: Optional[str] = None

    job_description: Optional[str] = None

    match_score: Optional[int] = Field(
        default=None,
        ge=0,
        le=100
    )

    recommendation: Optional[str] = None

    status: Optional[str] = None

    applied_at: Optional[datetime] = None


class JobApplicationResponse(BaseModel):
    id: int

    company: str
    role: str

    job_url: Optional[str] = None
    job_description: Optional[str] = None

    match_score: Optional[int] = None
    recommendation: Optional[str] = None

    status: str

    applied_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True