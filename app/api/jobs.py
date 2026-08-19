from fastapi import APIRouter, HTTPException

from app.schemas.jobs import (
    JobAnalysisRequest,
    JobAnalysisResponse
)

from app.services.job_service import analyze_job


router = APIRouter(
    prefix="/jobs",
    tags=["Jobs"]
)


@router.post(
    "/analyze",
    response_model=JobAnalysisResponse
)
def analyze_job_endpoint(request: JobAnalysisRequest):
    try:
        result = analyze_job(request.job_description)
        return JobAnalysisResponse(**result)

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Job analysis failed: {str(error)}"
        )