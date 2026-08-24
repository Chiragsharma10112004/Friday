from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.memory.database import SessionLocal
from app.application_pipeline.schemas import (
    ApplicationStatus,
    ApplicationPriority,
    ReferralStatus,
    FollowUpStatus,
    CreateApplicationRequest,
    UpdateApplicationRequest,
    ApplicationStatusTransitionRequest,
    MarkAppliedRequest,
    AddNoteRequest,
    ReferralRequest,
    FollowUpRequest,
    InterviewCreateRequest,
    InterviewUpdateRequest,
    ApplicationFilterParams,
    ApplicationResponse,
    ApplicationListResponse,
    ApplicationTimelineEventResponse,
    InterviewResponse,
    FollowUpCategoryResponse,
    PipelineSummaryResponse,
)
from app.application_pipeline.errors import PipelineErrorCode, PipelineException
from app.application_pipeline.service import default_pipeline_service

router = APIRouter(
    prefix="/applications",
    tags=["Applications"],
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _handle_pipeline_exception(e: PipelineException):
    status_code = status.HTTP_400_BAD_REQUEST
    if e.code in (
        PipelineErrorCode.APPLICATION_NOT_FOUND,
        PipelineErrorCode.OPPORTUNITY_NOT_FOUND,
        PipelineErrorCode.PROFILE_NOT_FOUND,
        PipelineErrorCode.INTERVIEW_NOT_FOUND,
    ):
        status_code = status.HTTP_404_NOT_FOUND
    elif e.code == PipelineErrorCode.DUPLICATE_APPLICATION:
        status_code = status.HTTP_409_CONFLICT
    elif e.code in (
        PipelineErrorCode.REFERRAL_INVALID,
        PipelineErrorCode.FOLLOW_UP_INVALID,
        PipelineErrorCode.APPLICATION_VALIDATION_ERROR,
    ):
        status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    elif e.code == PipelineErrorCode.PIPELINE_INTERNAL_ERROR:
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR

    raise HTTPException(
        status_code=status_code,
        detail={
            "code": e.code.value,
            "message": e.message,
            "application_id": e.application_id,
            "opportunity_id": e.opportunity_id,
        }
    )


# -------------------------------------------------------------
# 1. Collection & Aggregation Endpoints (Must precede /{application_id})
# -------------------------------------------------------------

@router.post(
    "",
    response_model=ApplicationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new tracked application manually"
)
def create_application_endpoint(
    request: CreateApplicationRequest,
    db: Session = Depends(get_db)
):
    try:
        return default_pipeline_service.create_application(request, db)
    except PipelineException as e:
        _handle_pipeline_exception(e)


@router.post(
    "/from-opportunity/{opportunity_id}",
    response_model=ApplicationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Convert a Phase 5 discovered opportunity into a tracked application"
)
def create_from_opportunity_endpoint(
    opportunity_id: int,
    db: Session = Depends(get_db)
):
    try:
        return default_pipeline_service.create_from_opportunity(opportunity_id, db)
    except PipelineException as e:
        _handle_pipeline_exception(e)


@router.get(
    "",
    response_model=ApplicationListResponse,
    summary="List applications with filtering, sorting, and pagination"
)
def list_applications_endpoint(
    status: Optional[ApplicationStatus] = None,
    company: Optional[str] = None,
    role: Optional[str] = None,
    priority: Optional[ApplicationPriority] = None,
    referral_status: Optional[ReferralStatus] = None,
    follow_up_status: Optional[FollowUpStatus] = None,
    sort_by: str = Query(default="created_at", description="created_at, updated_at, match_score, priority, next_follow_up_date"),
    sort_order: str = Query(default="desc", description="asc or desc"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    params = ApplicationFilterParams(
        status=status,
        company=company,
        role=role,
        priority=priority,
        referral_status=referral_status,
        follow_up_status=follow_up_status,
        sort_by=sort_by,
        sort_order=sort_order,
        page=page,
        page_size=page_size
    )
    return default_pipeline_service.list_applications(params, db)


@router.get(
    "/summary",
    response_model=PipelineSummaryResponse,
    summary="Get pipeline aggregated metrics, counts, and company breakdown"
)
def get_pipeline_summary_endpoint(
    db: Session = Depends(get_db)
):
    return default_pipeline_service.get_summary(db)


@router.get(
    "/follow-ups",
    response_model=FollowUpCategoryResponse,
    summary="Get categorized follow-ups (scheduled, due, overdue)"
)
def get_follow_ups_endpoint(
    db: Session = Depends(get_db)
):
    return default_pipeline_service.get_follow_ups(db)


@router.get(
    "/dashboard",
    summary="Backward-compatible application dashboard metrics"
)
def get_application_dashboard_endpoint(
    db: Session = Depends(get_db)
):
    summary = default_pipeline_service.get_summary(db)
    params = ApplicationFilterParams(sort_by="match_score", sort_order="desc", page=1, page_size=5)
    strongest_apps = default_pipeline_service.list_applications(params, db)

    return {
        "total_applications": summary.total_applications,
        "by_status": summary.status_counts,
        "average_match_score": summary.average_match_score,
        "strongest_applications": [
            {
                "id": a.id,
                "company": a.company,
                "role": a.role,
                "match_score": a.match_score,
                "status": a.status.value,
                "recommendation": a.recommendation,
            }
            for a in strongest_apps.items if a.match_score is not None
        ],
    }


# -------------------------------------------------------------
# 2. Individual Application Endpoints
# -------------------------------------------------------------

@router.get(
    "/{application_id}",
    response_model=ApplicationResponse,
    summary="Retrieve single tracked application"
)
def get_application_endpoint(
    application_id: int,
    db: Session = Depends(get_db)
):
    try:
        return default_pipeline_service.get_application(application_id, db)
    except PipelineException as e:
        _handle_pipeline_exception(e)


@router.patch(
    "/{application_id}",
    response_model=ApplicationResponse,
    summary="Update application details (company, role, priority, notes, etc.)"
)
def update_application_endpoint(
    application_id: int,
    request: UpdateApplicationRequest,
    db: Session = Depends(get_db)
):
    try:
        return default_pipeline_service.update_application(application_id, request, db)
    except PipelineException as e:
        _handle_pipeline_exception(e)


@router.post(
    "/{application_id}/status",
    response_model=ApplicationResponse,
    summary="Perform a validated lifecycle status transition"
)
def transition_status_endpoint(
    application_id: int,
    request: ApplicationStatusTransitionRequest,
    db: Session = Depends(get_db)
):
    try:
        return default_pipeline_service.transition_status(application_id, request, db)
    except PipelineException as e:
        _handle_pipeline_exception(e)


@router.post(
    "/{application_id}/mark-applied",
    response_model=ApplicationResponse,
    summary="Mark application as APPLIED (sets applied_at timestamp & timeline event)"
)
def mark_applied_endpoint(
    application_id: int,
    request: Optional[MarkAppliedRequest] = None,
    db: Session = Depends(get_db)
):
    try:
        req = request or MarkAppliedRequest()
        return default_pipeline_service.mark_applied(application_id, req, db)
    except PipelineException as e:
        _handle_pipeline_exception(e)


@router.get(
    "/{application_id}/timeline",
    response_model=List[ApplicationTimelineEventResponse],
    summary="Retrieve chronological audit timeline for application"
)
def get_timeline_endpoint(
    application_id: int,
    db: Session = Depends(get_db)
):
    try:
        return default_pipeline_service.get_timeline(application_id, db)
    except PipelineException as e:
        _handle_pipeline_exception(e)


@router.post(
    "/{application_id}/notes",
    response_model=ApplicationResponse,
    summary="Add an audit note to application"
)
def add_note_endpoint(
    application_id: int,
    request: AddNoteRequest,
    db: Session = Depends(get_db)
):
    try:
        return default_pipeline_service.add_note(application_id, request, db)
    except PipelineException as e:
        _handle_pipeline_exception(e)


@router.post(
    "/{application_id}/referral",
    response_model=ApplicationResponse,
    summary="Add or update referral status and contact metadata"
)
def update_referral_endpoint(
    application_id: int,
    request: ReferralRequest,
    db: Session = Depends(get_db)
):
    try:
        return default_pipeline_service.update_referral(application_id, request, db)
    except PipelineException as e:
        _handle_pipeline_exception(e)


@router.post(
    "/{application_id}/follow-up",
    response_model=ApplicationResponse,
    summary="Schedule a follow-up reminder date"
)
def schedule_follow_up_endpoint(
    application_id: int,
    request: FollowUpRequest,
    db: Session = Depends(get_db)
):
    try:
        return default_pipeline_service.schedule_follow_up(application_id, request, db)
    except PipelineException as e:
        _handle_pipeline_exception(e)


@router.post(
    "/{application_id}/follow-up/complete",
    response_model=ApplicationResponse,
    summary="Mark scheduled follow-up as completed"
)
def complete_follow_up_endpoint(
    application_id: int,
    db: Session = Depends(get_db)
):
    try:
        return default_pipeline_service.complete_follow_up(application_id, db)
    except PipelineException as e:
        _handle_pipeline_exception(e)


@router.post(
    "/{application_id}/interviews",
    response_model=InterviewResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create an interview round for application"
)
def create_interview_endpoint(
    application_id: int,
    request: InterviewCreateRequest,
    db: Session = Depends(get_db)
):
    try:
        return default_pipeline_service.create_interview(application_id, request, db)
    except PipelineException as e:
        _handle_pipeline_exception(e)


@router.get(
    "/{application_id}/interviews",
    response_model=List[InterviewResponse],
    summary="List all interview rounds for application"
)
def list_interviews_endpoint(
    application_id: int,
    db: Session = Depends(get_db)
):
    try:
        return default_pipeline_service.list_interviews(application_id, db)
    except PipelineException as e:
        _handle_pipeline_exception(e)


@router.patch(
    "/{application_id}/interviews/{interview_id}",
    response_model=InterviewResponse,
    summary="Update interview round status or scheduling details"
)
def update_interview_endpoint(
    application_id: int,
    interview_id: int,
    request: InterviewUpdateRequest,
    db: Session = Depends(get_db)
):
    try:
        return default_pipeline_service.update_interview(application_id, interview_id, request, db)
    except PipelineException as e:
        _handle_pipeline_exception(e)

