from sqlalchemy.orm import Session

from app.applications.models import JobApplication
from app.schemas.job_application import AnalyzeAndSaveRequest
from app.services.job_service import analyze_job


def analyze_and_save_job(
    request: AnalyzeAndSaveRequest,
    db: Session
):
    # Analyze the job using FRIDAY + your saved profile
    analysis = analyze_job(
        request.job_description,
        db
    )

    application = None

    # Save only if requested
    if request.save_application:

        application = JobApplication(
            company=request.company,
            role=request.role,
            job_url=request.job_url,
            job_description=request.job_description,

            match_score=analysis["match_score"],
            recommendation=analysis["recommendation"],

            status=request.status
        )

        db.add(application)
        db.commit()
        db.refresh(application)

    # Return FLAT response matching AnalyzeAndSaveResponse
    return {
        "application_id": (
            application.id
            if application
            else None
        ),

        "saved": application is not None,

        "match_score": analysis["match_score"],
        "recommendation": analysis["recommendation"],

        "strong_matches": analysis["strong_matches"],
        "project_matches": analysis["project_matches"],
        "partial_matches": analysis["partial_matches"],

        "missing_skills": analysis["missing_skills"],
        "learnable_skills": analysis["learnable_skills"],

        "reason": analysis["reason"],
        "resume_focus": analysis["resume_focus"],
        "interview_topics": analysis["interview_topics"]
    }