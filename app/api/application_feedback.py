from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.memory.database import SessionLocal
from app.application_feedback.schemas import (
    OutcomeFeedbackCreateRequest,
    OutcomeFeedbackResponse,
    AssetVersionCreateRequest,
    AssetVersionResponse,
    FieldIssueCreateRequest,
    FieldIssueResponse,
    AnalyticsSummaryResponse,
    ConversionFunnelResponse,
    PlatformPerformanceResponse,
    AssetPerformanceResponse,
    FeedbackSignalResponse,
    FeedbackRankRequest,
    FeedbackRankResponse,
)
from app.application_feedback.service import default_feedback_service

router = APIRouter(prefix="/feedback", tags=["Application Feedback & Analytics"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()



# ==========================================
# OUTCOME FEEDBACK ENDPOINTS
# ==========================================

@router.post(
    "/outcomes",
    response_model=OutcomeFeedbackResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Record structured application/interview outcome feedback"
)
def record_outcome(
    req: OutcomeFeedbackCreateRequest,
    db: Session = Depends(get_db)
):
    try:
        return default_feedback_service.record_outcome(db=db, req=req)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get(
    "/outcomes",
    response_model=List[OutcomeFeedbackResponse],
    summary="List all recorded outcome feedback records"
)
def list_outcomes(
    application_id: Optional[int] = Query(None, description="Filter by application ID"),
    profile_id: Optional[int] = Query(None, description="Filter by profile ID"),
    company: Optional[str] = Query(None, description="Filter by company name substring"),
    outcome_type: Optional[str] = Query(None, description="Filter by outcome type"),
    db: Session = Depends(get_db)
):
    return default_feedback_service.list_outcomes(
        db=db,
        application_id=application_id,
        profile_id=profile_id,
        company=company,
        outcome_type=outcome_type,
    )


@router.get(
    "/outcomes/{feedback_id}",
    response_model=OutcomeFeedbackResponse,
    summary="Get single outcome feedback details by ID"
)
def get_outcome(
    feedback_id: int,
    db: Session = Depends(get_db)
):
    res = default_feedback_service.get_outcome(db=db, feedback_id=feedback_id)
    if not res:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Outcome feedback {feedback_id} not found")
    return res


# ==========================================
# ASSET VERSIONING ENDPOINTS
# ==========================================

@router.post(
    "/assets/snapshot",
    response_model=AssetVersionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Snapshot tailored resume/cover-letter version for an application"
)
def snapshot_asset_version(
    req: AssetVersionCreateRequest,
    db: Session = Depends(get_db)
):
    try:
        return default_feedback_service.snapshot_asset_version(db=db, req=req)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get(
    "/assets/application/{application_id}",
    response_model=List[AssetVersionResponse],
    summary="Get asset version snapshots for a specific application"
)
def get_application_asset_versions(
    application_id: int,
    db: Session = Depends(get_db)
):
    return default_feedback_service.get_asset_versions(db=db, application_id=application_id)


# ==========================================
# FIELD ISSUE TRACKING ENDPOINTS
# ==========================================

@router.post(
    "/field-issues",
    response_model=FieldIssueResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Log form-field inspection, validation, or autofill execution issue"
)
def log_field_issue(
    req: FieldIssueCreateRequest,
    db: Session = Depends(get_db)
):
    return default_feedback_service.log_field_issue(db=db, req=req)


@router.get(
    "/field-issues",
    response_model=List[FieldIssueResponse],
    summary="List logged field execution and autofill issues"
)
def list_field_issues(
    application_id: Optional[int] = Query(None, description="Filter by application ID"),
    platform: Optional[str] = Query(None, description="Filter by ATS platform"),
    issue_type: Optional[str] = Query(None, description="Filter by issue type"),
    resolved: Optional[bool] = Query(None, description="Filter by resolution status"),
    db: Session = Depends(get_db)
):
    return default_feedback_service.list_field_issues(
        db=db,
        application_id=application_id,
        platform=platform,
        issue_type=issue_type,
        resolved=resolved,
    )


@router.post(
    "/field-issues/{issue_id}/resolve",
    response_model=FieldIssueResponse,
    summary="Mark a form-field issue as resolved"
)
def resolve_field_issue(
    issue_id: int,
    db: Session = Depends(get_db)
):
    res = default_feedback_service.resolve_field_issue(db=db, issue_id=issue_id)
    if not res:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Field issue {issue_id} not found")
    return res


# ==========================================
# ANALYTICS ENDPOINTS
# ==========================================

@router.get(
    "/analytics/summary",
    response_model=AnalyticsSummaryResponse,
    summary="Get comprehensive application pipeline conversion analytics"
)
def get_analytics_summary(db: Session = Depends(get_db)):
    return default_feedback_service.get_analytics_summary(db=db)


@router.get(
    "/analytics/funnel",
    response_model=ConversionFunnelResponse,
    summary="Get application conversion funnel metrics"
)
def get_funnel(db: Session = Depends(get_db)):
    return default_feedback_service.get_funnel(db=db)


@router.get(
    "/analytics/platforms",
    response_model=List[PlatformPerformanceResponse],
    summary="Get performance and issue metrics by ATS platform"
)
def get_platform_metrics(db: Session = Depends(get_db)):
    return default_feedback_service.get_platform_metrics(db=db)


@router.get(
    "/analytics/assets",
    response_model=List[AssetPerformanceResponse],
    summary="Get interview conversion performance by asset customization focus"
)
def get_asset_performance(db: Session = Depends(get_db)):
    return default_feedback_service.get_asset_performance(db=db)


# ==========================================
# LEARNING SIGNALS & FEEDBACK RANKING
# ==========================================

@router.get(
    "/signals",
    response_model=List[FeedbackSignalResponse],
    summary="List active learning signals derived from application feedback"
)
def list_signals(
    profile_id: Optional[int] = Query(None, description="Filter by profile ID"),
    db: Session = Depends(get_db)
):
    return default_feedback_service.list_signals(db=db, profile_id=profile_id)


@router.post(
    "/rank",
    response_model=FeedbackRankResponse,
    summary="Rank opportunity factoring in past feedback and rejection penalties"
)
def rank_opportunity(
    req: FeedbackRankRequest,
    db: Session = Depends(get_db)
):
    return default_feedback_service.rank_opportunity(db=db, req=req)
