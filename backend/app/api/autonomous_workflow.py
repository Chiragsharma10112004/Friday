from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.memory.database import SessionLocal
from app.autonomous_workflow.schemas import (
    WorkflowStatus,
    WorkflowPriority,
    ApprovalType,
    ApprovalStatus,
    PauseReason,
    WorkflowCreateRequest,
    WorkflowFromOpportunityRequest,
    WorkflowResponse,
    WorkflowListResponse,
    WorkflowStepListResponse,
    WorkflowApprovalListResponse,
    WorkflowApproveRequest,
    WorkflowRejectRequest,
    WorkflowActionLogListResponse,
    WorkflowPlanResponse,
    WorkflowQueueResponse,
    WorkflowDashboardResponse,
    WorkflowNextActionResponse,
    DiscoveryRunResponse,
    ReferralUpdateRequest,
)
from app.autonomous_workflow.errors import WorkflowErrorCode, WorkflowException
from app.autonomous_workflow.service import default_workflow_service

router = APIRouter(
    prefix="/workflow",
    tags=["Autonomous Workflow Orchestration"],
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _handle_workflow_exception(e: WorkflowException):
    status_code = status.HTTP_400_BAD_REQUEST
    if e.code in (
        WorkflowErrorCode.WORKFLOW_NOT_FOUND,
        WorkflowErrorCode.APPLICATION_NOT_FOUND,
        WorkflowErrorCode.OPPORTUNITY_NOT_FOUND,
        WorkflowErrorCode.APPROVAL_NOT_FOUND,
    ):
        status_code = status.HTTP_404_NOT_FOUND
    elif e.code == WorkflowErrorCode.DUPLICATE_WORKFLOW:
        status_code = status.HTTP_409_CONFLICT
    elif e.code == WorkflowErrorCode.WORKFLOW_VALIDATION_ERROR:
        status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    elif e.code in (
        WorkflowErrorCode.WORKFLOW_INTERNAL_ERROR,
        WorkflowErrorCode.ASSET_GENERATION_FAILED,
        WorkflowErrorCode.APPLICATION_INSPECTION_FAILED,
        WorkflowErrorCode.AUTOFILL_FAILED,
        WorkflowErrorCode.DISCOVERY_FAILED,
    ):
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR

    raise HTTPException(
        status_code=status_code,
        detail={
            "code": e.code.value,
            "message": e.message,
            "workflow_id": e.workflow_id,
            "step_id": e.step_id,
            "approval_id": e.approval_id,
            "details": e.details,
        }
    )


# -------------------------------------------------------------
# Endpoints
# -------------------------------------------------------------

@router.post(
    "",
    response_model=WorkflowResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new workflow manually"
)
def create_workflow_endpoint(
    req: WorkflowCreateRequest,
    db: Session = Depends(get_db)
):
    try:
        return default_workflow_service.create_workflow(
            company=req.company,
            role=req.role,
            source_url=req.source_url,
            source_platform=req.source_platform,
            priority=req.priority,
            opportunity_id=req.opportunity_id,
            application_id=req.application_id,
            job_description=req.job_description,
            match_score=req.match_score,
            db=db
        )
    except WorkflowException as e:
        _handle_workflow_exception(e)


@router.post(
    "/from-opportunity/{opportunity_id}",
    response_model=WorkflowResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a workflow from a discovered opportunity"
)
def create_from_opportunity_endpoint(
    opportunity_id: int,
    req: Optional[WorkflowFromOpportunityRequest] = None,
    db: Session = Depends(get_db)
):
    try:
        prio = req.priority if req else None
        return default_workflow_service.create_from_opportunity(
            opportunity_id=opportunity_id,
            priority=prio,
            db=db
        )
    except WorkflowException as e:
        _handle_workflow_exception(e)


@router.get(
    "/queue",
    response_model=WorkflowQueueResponse,
    summary="Get prioritized workflow queue organized by actionable categories"
)
def get_workflow_queue_endpoint(
    db: Session = Depends(get_db)
):
    try:
        return default_workflow_service.get_queue(db=db)
    except WorkflowException as e:
        _handle_workflow_exception(e)


@router.get(
    "/dashboard",
    response_model=WorkflowDashboardResponse,
    summary="Get workflow analytics dashboard metrics"
)
def get_workflow_dashboard_endpoint(
    db: Session = Depends(get_db)
):
    try:
        return default_workflow_service.get_dashboard(db=db)
    except WorkflowException as e:
        _handle_workflow_exception(e)


@router.get(
    "",
    response_model=WorkflowListResponse,
    summary="List workflows with filtering and pagination"
)
def list_workflows_endpoint(
    priority: Optional[WorkflowPriority] = None,
    status: Optional[WorkflowStatus] = None,
    company: Optional[str] = None,
    min_match_score: Optional[int] = None,
    user_action_required: Optional[bool] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    try:
        return default_workflow_service.list_workflows(
            priority=priority,
            status=status,
            company=company,
            min_match_score=min_match_score,
            user_action_required=user_action_required,
            skip=skip,
            limit=limit,
            db=db
        )
    except WorkflowException as e:
        _handle_workflow_exception(e)


@router.get(
    "/{workflow_id}",
    response_model=WorkflowResponse,
    summary="Get workflow details"
)
def get_workflow_endpoint(
    workflow_id: int,
    db: Session = Depends(get_db)
):
    try:
        return default_workflow_service.get_workflow(workflow_id=workflow_id, db=db)
    except WorkflowException as e:
        _handle_workflow_exception(e)


@router.post(
    "/{workflow_id}/start",
    response_model=WorkflowResponse,
    summary="Start workflow execution"
)
def start_workflow_endpoint(
    workflow_id: int,
    db: Session = Depends(get_db)
):
    try:
        return default_workflow_service.start_workflow(workflow_id=workflow_id, db=db)
    except WorkflowException as e:
        _handle_workflow_exception(e)


@router.post(
    "/{workflow_id}/approve",
    response_model=WorkflowResponse,
    summary="Approve a workflow checkpoint"
)
def approve_checkpoint_endpoint(
    workflow_id: int,
    req: Optional[WorkflowApproveRequest] = None,
    db: Session = Depends(get_db)
):
    try:
        appr_type = req.approval_type if req else None
        appr_by = req.approved_by if req else "user"
        reason = req.reason if req else None
        return default_workflow_service.approve_checkpoint(
            workflow_id=workflow_id,
            approval_type=appr_type,
            approved_by=appr_by,
            reason=reason,
            db=db
        )
    except WorkflowException as e:
        _handle_workflow_exception(e)


@router.post(
    "/{workflow_id}/reject",
    response_model=WorkflowResponse,
    summary="Reject a workflow checkpoint"
)
def reject_checkpoint_endpoint(
    workflow_id: int,
    req: Optional[WorkflowRejectRequest] = None,
    db: Session = Depends(get_db)
):
    try:
        appr_type = req.approval_type if req else None
        rej_by = req.rejected_by if req else "user"
        reason = req.reason if req else "Rejected by user"
        return default_workflow_service.reject_checkpoint(
            workflow_id=workflow_id,
            approval_type=appr_type,
            rejected_by=rej_by,
            reason=reason,
            db=db
        )
    except WorkflowException as e:
        _handle_workflow_exception(e)


@router.post(
    "/{workflow_id}/pause",
    response_model=WorkflowResponse,
    summary="Pause active workflow"
)
def pause_workflow_endpoint(
    workflow_id: int,
    reason: PauseReason = PauseReason.USER_PAUSED,
    db: Session = Depends(get_db)
):
    try:
        return default_workflow_service.pause_workflow(
            workflow_id=workflow_id,
            reason=reason,
            db=db
        )
    except WorkflowException as e:
        _handle_workflow_exception(e)


@router.post(
    "/{workflow_id}/resume",
    response_model=WorkflowResponse,
    summary="Resume paused workflow"
)
def resume_workflow_endpoint(
    workflow_id: int,
    db: Session = Depends(get_db)
):
    try:
        return default_workflow_service.resume_workflow(
            workflow_id=workflow_id,
            db=db
        )
    except WorkflowException as e:
        _handle_workflow_exception(e)


@router.post(
    "/{workflow_id}/retry",
    response_model=WorkflowResponse,
    summary="Retry a failed or paused workflow"
)
def retry_workflow_endpoint(
    workflow_id: int,
    db: Session = Depends(get_db)
):
    try:
        return default_workflow_service.retry_workflow(
            workflow_id=workflow_id,
            db=db
        )
    except WorkflowException as e:
        _handle_workflow_exception(e)


@router.post(
    "/{workflow_id}/cancel",
    response_model=WorkflowResponse,
    summary="Cancel active workflow"
)
def cancel_workflow_endpoint(
    workflow_id: int,
    reason: str = "Cancelled by user",
    db: Session = Depends(get_db)
):
    try:
        return default_workflow_service.cancel_workflow(
            workflow_id=workflow_id,
            reason=reason,
            db=db
        )
    except WorkflowException as e:
        _handle_workflow_exception(e)


@router.get(
    "/{workflow_id}/plan",
    response_model=WorkflowPlanResponse,
    summary="Get execution plan for workflow"
)
def get_workflow_plan_endpoint(
    workflow_id: int,
    db: Session = Depends(get_db)
):
    try:
        return default_workflow_service.get_plan(workflow_id=workflow_id, db=db)
    except WorkflowException as e:
        _handle_workflow_exception(e)


@router.get(
    "/{workflow_id}/steps",
    response_model=WorkflowStepListResponse,
    summary="Get workflow execution steps"
)
def get_workflow_steps_endpoint(
    workflow_id: int,
    db: Session = Depends(get_db)
):
    try:
        return default_workflow_service.get_steps(workflow_id=workflow_id, db=db)
    except WorkflowException as e:
        _handle_workflow_exception(e)


@router.get(
    "/{workflow_id}/actions",
    response_model=WorkflowActionLogListResponse,
    summary="Get audit and action history for workflow"
)
def get_workflow_actions_endpoint(
    workflow_id: int,
    db: Session = Depends(get_db)
):
    try:
        return default_workflow_service.get_actions(workflow_id=workflow_id, db=db)
    except WorkflowException as e:
        _handle_workflow_exception(e)


@router.get(
    "/{workflow_id}/approvals",
    response_model=WorkflowApprovalListResponse,
    summary="Get approvals for workflow"
)
def get_workflow_approvals_endpoint(
    workflow_id: int,
    status: Optional[ApprovalStatus] = None,
    db: Session = Depends(get_db)
):
    try:
        return default_workflow_service.get_approvals(
            workflow_id=workflow_id,
            status=status,
            db=db
        )
    except WorkflowException as e:
        _handle_workflow_exception(e)


@router.get(
    "/{workflow_id}/next-action",
    response_model=WorkflowNextActionResponse,
    summary="Get recommended next action for workflow"
)
def get_workflow_next_action_endpoint(
    workflow_id: int,
    db: Session = Depends(get_db)
):
    try:
        return default_workflow_service.get_next_action(workflow_id=workflow_id, db=db)
    except WorkflowException as e:
        _handle_workflow_exception(e)


@router.post(
    "/{workflow_id}/assets/generate",
    response_model=Dict[str, Any],
    summary="Generate tailored application assets via Phase 3"
)
def generate_assets_endpoint(
    workflow_id: int,
    db: Session = Depends(get_db)
):
    try:
        return default_workflow_service.generate_assets(workflow_id=workflow_id, db=db)
    except WorkflowException as e:
        _handle_workflow_exception(e)


@router.post(
    "/{workflow_id}/application/inspect",
    response_model=Dict[str, Any],
    summary="Inspect application form via Phase 4"
)
def inspect_application_endpoint(
    workflow_id: int,
    db: Session = Depends(get_db)
):
    try:
        return default_workflow_service.inspect_application(workflow_id=workflow_id, db=db)
    except WorkflowException as e:
        _handle_workflow_exception(e)


@router.post(
    "/{workflow_id}/application/autofill",
    response_model=Dict[str, Any],
    summary="Autofill approved non-sensitive fields via Phase 4"
)
def autofill_fields_endpoint(
    workflow_id: int,
    approved_field_ids: Optional[List[str]] = None,
    db: Session = Depends(get_db)
):
    try:
        return default_workflow_service.autofill_approved_fields(
            workflow_id=workflow_id,
            approved_field_ids=approved_field_ids,
            db=db
        )
    except WorkflowException as e:
        _handle_workflow_exception(e)


@router.post(
    "/{workflow_id}/referral",
    response_model=Dict[str, Any],
    summary="Update referral tracking information for workflow"
)
def update_referral_endpoint(
    workflow_id: int,
    req: ReferralUpdateRequest,
    db: Session = Depends(get_db)
):
    try:
        return default_workflow_service.update_referral(
            workflow_id=workflow_id,
            referral_data=req,
            db=db
        )
    except WorkflowException as e:
        _handle_workflow_exception(e)


@router.post(
    "/{workflow_id}/confirm-manual-submission",
    response_model=WorkflowResponse,
    summary="Confirm that the application was manually submitted on the external portal"
)
def confirm_manual_submission_endpoint(
    workflow_id: int,
    notes: Optional[str] = None,
    db: Session = Depends(get_db)
):
    try:
        return default_workflow_service.confirm_manual_submission(
            workflow_id=workflow_id,
            notes=notes,
            db=db
        )
    except WorkflowException as e:
        _handle_workflow_exception(e)


@router.post(
    "/discovery/run",
    response_model=DiscoveryRunResponse,
    summary="Run manual discovery and workflow queue population cycle"
)
def run_discovery_endpoint(
    min_score_threshold: int = Query(70, ge=0, le=100),
    db: Session = Depends(get_db)
):
    try:
        return default_workflow_service.run_discovery(
            min_score_threshold=min_score_threshold,
            db=db
        )
    except WorkflowException as e:
        _handle_workflow_exception(e)

