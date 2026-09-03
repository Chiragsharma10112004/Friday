from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.memory.database import SessionLocal
from app.career_intelligence.schemas import (
    RecommendationType,
    RecommendationStatus,
    ActionPriority,
    ActionItemResponse,
    TodayActionQueueResponse,
    DashboardIntelligenceResponse,
    ApplicationHealthItem,
    ApplicationHealthListResponse,
    DailyBriefingResponse,
    WeeklyBriefingResponse,
    RefreshResponse,
)
from app.career_intelligence.errors import (
    CareerIntelligenceErrorCode,
    CareerIntelligenceException,
)
from app.career_intelligence.service import default_career_intelligence_service

router = APIRouter(
    prefix="/career-intelligence",
    tags=["Career Intelligence"],
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _handle_intelligence_exception(e: CareerIntelligenceException):
    status_code = status.HTTP_400_BAD_REQUEST
    if e.code in (
        CareerIntelligenceErrorCode.RECOMMENDATION_NOT_FOUND,
        CareerIntelligenceErrorCode.APPLICATION_NOT_FOUND,
        CareerIntelligenceErrorCode.OPPORTUNITY_NOT_FOUND,
    ):
        status_code = status.HTTP_404_NOT_FOUND
    elif e.code == CareerIntelligenceErrorCode.CAREER_INTELLIGENCE_VALIDATION_ERROR:
        status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    elif e.code == CareerIntelligenceErrorCode.CAREER_INTELLIGENCE_INTERNAL_ERROR:
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR

    raise HTTPException(
        status_code=status_code,
        detail={
            "code": e.code.value,
            "message": e.message,
            "recommendation_id": e.recommendation_id,
            "application_id": e.application_id,
            "opportunity_id": e.opportunity_id,
        }
    )


@router.get(
    "/today",
    response_model=TodayActionQueueResponse,
    summary="Get today's prioritized action queue"
)
def get_today_actions_endpoint(
    db: Session = Depends(get_db)
):
    try:
        return default_career_intelligence_service.get_today_actions(db)
    except CareerIntelligenceException as e:
        _handle_intelligence_exception(e)


@router.get(
    "/next-actions",
    response_model=List[ActionItemResponse],
    summary="Get active next-action recommendations with filtering"
)
def get_next_actions_endpoint(
    priority: Optional[ActionPriority] = None,
    recommendation_type: Optional[RecommendationType] = None,
    application_id: Optional[int] = None,
    opportunity_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    try:
        return default_career_intelligence_service.get_next_actions(
            db=db,
            priority=priority,
            recommendation_type=recommendation_type,
            application_id=application_id,
            opportunity_id=opportunity_id,
            status=RecommendationStatus.ACTIVE
        )
    except CareerIntelligenceException as e:
        _handle_intelligence_exception(e)


@router.get(
    "/dashboard",
    response_model=DashboardIntelligenceResponse,
    summary="Get intelligence overview dashboard metrics and application health breakdown"
)
def get_intelligence_dashboard_endpoint(
    db: Session = Depends(get_db)
):
    try:
        return default_career_intelligence_service.get_dashboard(db)
    except CareerIntelligenceException as e:
        _handle_intelligence_exception(e)


@router.get(
    "/application-health",
    response_model=ApplicationHealthListResponse,
    summary="Get application health diagnostics across all active applications"
)
def get_all_application_health_endpoint(
    db: Session = Depends(get_db)
):
    try:
        return default_career_intelligence_service.get_application_health(db)
    except CareerIntelligenceException as e:
        _handle_intelligence_exception(e)


@router.get(
    "/application-health/{application_id}",
    response_model=ApplicationHealthItem,
    summary="Get health diagnostic evaluation for a specific application"
)
def get_single_application_health_endpoint(
    application_id: int,
    db: Session = Depends(get_db)
):
    try:
        return default_career_intelligence_service.get_application_health(db, application_id=application_id)
    except CareerIntelligenceException as e:
        _handle_intelligence_exception(e)


@router.get(
    "/daily-briefing",
    response_model=DailyBriefingResponse,
    summary="Generate daily career briefing"
)
def get_daily_briefing_endpoint(
    db: Session = Depends(get_db)
):
    try:
        return default_career_intelligence_service.get_daily_briefing(db)
    except CareerIntelligenceException as e:
        _handle_intelligence_exception(e)


@router.get(
    "/weekly-briefing",
    response_model=WeeklyBriefingResponse,
    summary="Generate weekly pipeline briefing"
)
def get_weekly_briefing_endpoint(
    db: Session = Depends(get_db)
):
    try:
        return default_career_intelligence_service.get_weekly_briefing(db)
    except CareerIntelligenceException as e:
        _handle_intelligence_exception(e)


@router.post(
    "/recommendations/{recommendation_id}/dismiss",
    response_model=ActionItemResponse,
    summary="Dismiss an active recommendation"
)
def dismiss_recommendation_endpoint(
    recommendation_id: int,
    db: Session = Depends(get_db)
):
    try:
        return default_career_intelligence_service.dismiss_recommendation(recommendation_id, db)
    except CareerIntelligenceException as e:
        _handle_intelligence_exception(e)


@router.post(
    "/recommendations/{recommendation_id}/complete",
    response_model=ActionItemResponse,
    summary="Mark an active recommendation as completed"
)
def complete_recommendation_endpoint(
    recommendation_id: int,
    db: Session = Depends(get_db)
):
    try:
        return default_career_intelligence_service.complete_recommendation(recommendation_id, db)
    except CareerIntelligenceException as e:
        _handle_intelligence_exception(e)


@router.post(
    "/recommendations/refresh",
    response_model=RefreshResponse,
    summary="Recalculate recommendations across applications and opportunities without external actions"
)
def refresh_recommendations_endpoint(
    db: Session = Depends(get_db)
):
    try:
        return default_career_intelligence_service.refresh_recommendations(db)
    except CareerIntelligenceException as e:
        _handle_intelligence_exception(e)
