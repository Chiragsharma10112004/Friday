from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.memory.database import SessionLocal
from app.job_discovery.schemas import (
    DiscoveredJob,
    OpportunityFilterParams,
    OpportunityListResponse,
    UpdateOpportunityStatusRequest,
    PipelineStatus,
)
from app.job_discovery.errors import DiscoveryErrorCode, DiscoveryException
from app.job_discovery.service import default_discovery_service
from app.application_assets.schemas import ApplicationAssetResponse
from app.application_automation.schemas import InspectApplicationResponse

router = APIRouter(
    prefix="/opportunities",
    tags=["Opportunities Pipeline"]
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get(
    "",
    response_model=OpportunityListResponse,
    summary="List opportunities with filtering, sorting, and pagination"
)
def list_opportunities_endpoint(
    min_match_score: Optional[int] = Query(None, ge=0, le=100),
    company: Optional[str] = None,
    title: Optional[str] = None,
    provider: Optional[str] = None,
    location: Optional[str] = None,
    is_remote: Optional[bool] = None,
    status: Optional[PipelineStatus] = None,
    sort_by: str = Query("match_score", regex="^(match_score|newest|company|title)$"),
    sort_order: str = Query("desc", regex="^(asc|desc)$"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    params = OpportunityFilterParams(
        min_match_score=min_match_score,
        company=company,
        title=title,
        provider=provider,
        location=location,
        is_remote=is_remote,
        status=status,
        sort_by=sort_by,
        sort_order=sort_order,
        page=page,
        page_size=page_size,
    )
    return default_discovery_service.list_opportunities(params, db)


@router.get(
    "/{opportunity_id}",
    response_model=DiscoveredJob,
    summary="Retrieve complete opportunity details"
)
def get_opportunity_endpoint(
    opportunity_id: int,
    db: Session = Depends(get_db)
):
    try:
        return default_discovery_service.get_opportunity(opportunity_id, db)
    except DiscoveryException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": e.code.value, "message": e.message}
        )


@router.patch(
    "/{opportunity_id}/status",
    response_model=DiscoveredJob,
    summary="Update opportunity pipeline status with transition validation"
)
def update_opportunity_status_endpoint(
    opportunity_id: int,
    request: UpdateOpportunityStatusRequest,
    db: Session = Depends(get_db)
):
    try:
        return default_discovery_service.update_opportunity_status(opportunity_id, request.status, db)
    except DiscoveryException as e:
        status_code = status.HTTP_400_BAD_REQUEST
        if e.code == DiscoveryErrorCode.OPPORTUNITY_NOT_FOUND:
            status_code = status.HTTP_404_NOT_FOUND
        elif e.code == DiscoveryErrorCode.INVALID_STATUS_TRANSITION:
            status_code = status.HTTP_422_UNPROCESSABLE_ENTITY

        raise HTTPException(
            status_code=status_code,
            detail={"code": e.code.value, "message": e.message}
        )


@router.post(
    "/{opportunity_id}/analyze",
    summary="Trigger deep Phase 1 job analysis on opportunity"
)
def analyze_opportunity_endpoint(
    opportunity_id: int,
    db: Session = Depends(get_db)
):
    try:
        return default_discovery_service.analyze_opportunity(opportunity_id, db)
    except DiscoveryException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": e.code.value, "message": e.message}
        )


@router.post(
    "/{opportunity_id}/generate-assets",
    response_model=ApplicationAssetResponse,
    summary="Generate Phase 3 tailored application assets for opportunity"
)
def generate_opportunity_assets_endpoint(
    opportunity_id: int,
    db: Session = Depends(get_db)
):
    try:
        return default_discovery_service.generate_opportunity_assets(opportunity_id, db)
    except DiscoveryException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": e.code.value, "message": e.message}
        )


@router.post(
    "/{opportunity_id}/prepare-application",
    response_model=InspectApplicationResponse,
    summary="Prepare opportunity for Phase 4 browser-assisted application assistance"
)
def prepare_opportunity_application_endpoint(
    opportunity_id: int,
    db: Session = Depends(get_db)
):
    try:
        return default_discovery_service.prepare_opportunity_application(opportunity_id, db)
    except DiscoveryException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": e.code.value, "message": e.message}
        )
