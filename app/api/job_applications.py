from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.memory.database import SessionLocal
from app.schemas.job_application import (
    AnalyzeAndSaveRequest,
    AnalyzeAndSaveResponse,
)
from app.services.job_application_service import analyze_and_save_job


router = APIRouter(
    prefix="/job-applications",
    tags=["Job Applications"],
)


def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


@router.post(
    "/analyze-and-save",
    response_model=AnalyzeAndSaveResponse,
)
def analyze_and_save_job_endpoint(
    request: AnalyzeAndSaveRequest,
    db: Session = Depends(get_db),
):
    return analyze_and_save_job(
        db,
        request,
    )