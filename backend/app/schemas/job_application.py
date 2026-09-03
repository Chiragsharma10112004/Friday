from typing import Optional

from pydantic import BaseModel, Field


class AnalyzeAndSaveRequest(BaseModel):
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

    job_description: str = Field(
        ...,
        min_length=50
    )

    job_url: Optional[str] = None

    save_application: bool = True

    status: str = "NOT_APPLIED"


class AnalyzeAndSaveResponse(BaseModel):
    application_id: Optional[int] = None
    saved: bool

    match_score: int
    recommendation: str

    strong_matches: list[str]
    project_matches: list[str]
    partial_matches: list[str]

    missing_skills: list[str]
    learnable_skills: list[str]

    reason: str
    resume_focus: str
    interview_topics: list[str]