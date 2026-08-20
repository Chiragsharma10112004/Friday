from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.memory.database import SessionLocal

from app.schemas.jobs import (
    JobAnalysisRequest,
    JobAnalysisResponse
)

from app.services.job_service import analyze_job


router = APIRouter(
    prefix="/jobs",
    tags=["Jobs"]
)


def get_db():
    db = SessionLocal()

    try:
        yield db

    finally:
        db.close()


@router.post(
    "/analyze",
    response_model=JobAnalysisResponse
)
def analyze_job_endpoint(
    request: JobAnalysisRequest,
    db: Session = Depends(get_db)
):
    try:
        result = analyze_job(
            request.job_description,
            db
        )

        return JobAnalysisResponse(
            **result
        )

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Job analysis failed: {str(error)}"
        )