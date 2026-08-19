from sqlalchemy.orm import Session

from app.schemas.job_application import (
    AnalyzeAndSaveRequest,
    AnalyzeAndSaveResponse,
)
from app.schemas.applications import JobApplicationCreate
from app.services.application_service import create_application
from app.services.job_service import analyze_job


def analyze_and_save_job(
    db: Session,
    request: AnalyzeAndSaveRequest,
) -> AnalyzeAndSaveResponse:

    analysis = analyze_job(
        request.job_description
    )

    application_id = None

    if request.save_application:
        application = create_application(
            db,
            JobApplicationCreate(
                company=request.company,
                role=request.role,
                job_url=request.job_url,
                job_description=request.job_description,
                match_score=analysis["match_score"],
                recommendation=analysis["recommendation"],
                status=request.status,
            ),
        )

        application_id = application.id

    return AnalyzeAndSaveResponse(
        application_id=application_id,
        saved=request.save_application,
        match_score=analysis["match_score"],
        recommendation=analysis["recommendation"],
        strong_matches=analysis.get("strong_matches", []),
        project_matches=analysis.get("project_matches", []),
        partial_matches=analysis.get("partial_matches", []),
        missing_skills=analysis.get("missing_skills", []),
        learnable_skills=analysis.get("learnable_skills", []),
        reason=analysis.get("reason", ""),
        resume_focus=analysis.get("resume_focus", ""),
        interview_topics=analysis.get("interview_topics", []),
    )