from pydantic import BaseModel, Field
from typing import List


class JobAnalysisRequest(BaseModel):
    job_description: str = Field(
        ...,
        min_length=50,
        description="Complete job description"
    )


class JobAnalysisResponse(BaseModel):
    match_score: int
    recommendation: str

    strong_matches: List[str]
    project_matches: List[str]
    partial_matches: List[str]

    missing_skills: List[str]
    learnable_skills: List[str]

    reason: str
    resume_focus: str
    interview_topics: List[str]