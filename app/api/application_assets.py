from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.memory.database import SessionLocal
from app.application_assets.schemas import (
    ApplicationAssetRequest,
    ApplicationAssetResponse,
)
from app.application_assets.service import default_asset_service

router = APIRouter(
    prefix="/application-assets",
    tags=["Application Assets"]
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post(
    "/generate",
    response_model=ApplicationAssetResponse,
    summary="Generate tailored application assets from job data"
)
def generate_application_assets_endpoint(
    request: ApplicationAssetRequest,
    db: Session = Depends(get_db)
):
    """
    Synthesize tailored application materials (Resume, Cover Letter, Recruiter Message,
    Skill Gap Analysis, Application Summary) based on the candidate's verified profile
    and target job requirements.
    """
    try:
        return default_asset_service.generate_assets(request, db)
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Asset generation failed: {str(e)}"
        )

