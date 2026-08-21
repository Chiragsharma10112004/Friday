from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.memory.database import SessionLocal
from app.schemas.jobs import (
    JobAnalysisRequest,
    JobAnalysisResponse,
)
from app.services.job_service import analyze_job
from app.ingestion.schemas import IngestJobRequest, IngestJobResponse
from app.ingestion.service import default_ingestion_service

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
    "/ingest",
    response_model=IngestJobResponse,
    summary="Ingest and parse a job posting from a URL"
)
def ingest_job_endpoint(request: IngestJobRequest):
    """
    Accepts a public job URL, verifies safety against SSRF, identifies the platform,
    extracts structured fields, and returns a normalized job posting.
    Does NOT analyze with LLM or save to database.
    """
    return default_ingestion_service.ingest_job(request)


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