import os
import sys

BASE_DIR = r"c:\Users\surbh\OneDrive\Desktop\Friday\backend"

FILES = {}

FILES["app/autonomous_workflow/discovery_scheduler.py"] = '''import logging
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.autonomous_workflow.models import AutonomousWorkflow
from app.autonomous_workflow.schemas import (
    WorkflowStatus,
    WorkflowPriority,
    DiscoveryRunResponse,
)
from app.autonomous_workflow.job_ranker import JobRankerEngine
from app.autonomous_workflow.repository import WorkflowRepository
from app.job_discovery.models import DiscoveredOpportunity
from app.profile.models import UserProfile

logger = logging.getLogger("friday.autonomous_workflow.discovery")


class DiscoveryScheduler:
    """
    Service abstraction for running automated job discovery cycles, ranking candidate opportunities,
    and creating queued autonomous workflows for top-tier matches.
    """

    DEFAULT_MIN_SCORE = 70

    @classmethod
    def run_discovery_cycle(
        cls,
        db: Session,
        min_score_threshold: int = DEFAULT_MIN_SCORE,
        profile_id: Optional[int] = None
    ) -> DiscoveryRunResponse:
        """
        Scans discovered opportunities, filters by score threshold, and initializes workflows.
        """
        query = db.query(DiscoveredOpportunity).filter(
            DiscoveredOpportunity.match_score >= min_score_threshold,
            DiscoveredOpportunity.status.notin_(["ARCHIVED", "REJECTED", "APPLIED"])
        )

        opportunities = query.order_by(desc(DiscoveredOpportunity.match_score)).all()

        workflows_created = 0
        workflows_queued = 0

        for opp in opportunities:
            existing_wf = WorkflowRepository.get_workflow_by_opportunity(db, opp.id)
            if existing_wf:
                continue

            ranking = JobRankerEngine.rank_job(
                match_score=opp.match_score,
                recommendation=opp.recommendation,
            )

            init_status = WorkflowStatus.QUEUED_FOR_REVIEW
            if (opp.match_score or 0) >= 85:
                init_status = WorkflowStatus.AWAITING_APPROVAL

            try:
                wf = WorkflowRepository.create_workflow(
                    db=db,
                    company=opp.company,
                    role=opp.title,
                    source_url=opp.source_url or opp.application_url,
                    source_platform=opp.provider,
                    priority=ranking.priority,
                    profile_id=profile_id,
                    opportunity_id=opp.id,
                    match_score=opp.match_score,
                    initial_status=init_status,
                    metadata={"ranking_reasons": ranking.reasons}
                )
                workflows_created += 1
                workflows_queued += 1
            except Exception as e:
                logger.warning(f"Could not auto-create workflow for opportunity {opp.id}: {e}")

        return DiscoveryRunResponse(
            success=True,
            opportunities_discovered=len(opportunities),
            workflows_created=workflows_created,
            workflows_queued=workflows_queued,
            min_score_threshold=min_score_threshold,
        )

    @classmethod
    def run_profile_discovery(
        cls,
        db: Session,
        profile_id: int,
        min_score_threshold: int = DEFAULT_MIN_SCORE
    ) -> DiscoveryRunResponse:
        return cls.run_discovery_cycle(db, min_score_threshold=min_score_threshold, profile_id=profile_id)

    @classmethod
    def run_all_active_profiles(
        cls,
        db: Session,
        min_score_threshold: int = DEFAULT_MIN_SCORE
    ) -> DiscoveryRunResponse:
        profile = db.query(UserProfile).first()
        return cls.run_discovery_cycle(db, min_score_threshold=min_score_threshold, profile_id=profile.id if profile else None)
'''

FILES["app/autonomous_workflow/__init__.py"] = '''from app.autonomous_workflow.models import (
    AutonomousWorkflow,
    WorkflowStep,
    WorkflowApproval,
    WorkflowActionLog,
    WorkflowRetry,
)
from app.autonomous_workflow.schemas import (
    WorkflowStatus,
    WorkflowPriority,
    WorkflowStepStatus,
    ApprovalType,
    ApprovalStatus,
    UserActionType,
    PauseReason,
    WorkflowActionType,
    WorkflowCreateRequest,
    WorkflowFromOpportunityRequest,
    WorkflowResponse,
    WorkflowListResponse,
    WorkflowStepResponse,
    WorkflowStepListResponse,
    WorkflowApprovalResponse,
    WorkflowApprovalListResponse,
    WorkflowApproveRequest,
    WorkflowRejectRequest,
    WorkflowActionLogResponse,
    WorkflowActionLogListResponse,
    WorkflowPlanStep,
    WorkflowPlanResponse,
    WorkflowQueueItem,
    WorkflowQueueResponse,
    WorkflowDashboardResponse,
    WorkflowNextActionResponse,
    DiscoveryRunResponse,
    ReferralUpdateRequest,
)
from app.autonomous_workflow.errors import (
    WorkflowErrorCode,
    WorkflowException,
)
from app.autonomous_workflow.workflow_state import WorkflowStateMachine
from app.autonomous_workflow.job_ranker import JobRankerEngine, JobRankingResult
from app.autonomous_workflow.application_planner import ApplicationPlanner
from app.autonomous_workflow.referral_manager import WorkflowReferralManager
from app.autonomous_workflow.discovery_scheduler import DiscoveryScheduler
from app.autonomous_workflow.orchestrator import AutonomousWorkflowOrchestrator
from app.autonomous_workflow.repository import WorkflowRepository
from app.autonomous_workflow.service import WorkflowService, default_workflow_service

__all__ = [
    "AutonomousWorkflow",
    "WorkflowStep",
    "WorkflowApproval",
    "WorkflowActionLog",
    "WorkflowRetry",
    "WorkflowStatus",
    "WorkflowPriority",
    "WorkflowStepStatus",
    "ApprovalType",
    "ApprovalStatus",
    "UserActionType",
    "PauseReason",
    "WorkflowActionType",
    "WorkflowCreateRequest",
    "WorkflowFromOpportunityRequest",
    "WorkflowResponse",
    "WorkflowListResponse",
    "WorkflowStepResponse",
    "WorkflowStepListResponse",
    "WorkflowApprovalResponse",
    "WorkflowApprovalListResponse",
    "WorkflowApproveRequest",
    "WorkflowRejectRequest",
    "WorkflowActionLogResponse",
    "WorkflowActionLogListResponse",
    "WorkflowPlanStep",
    "WorkflowPlanResponse",
    "WorkflowQueueItem",
    "WorkflowQueueResponse",
    "WorkflowDashboardResponse",
    "WorkflowNextActionResponse",
    "DiscoveryRunResponse",
    "ReferralUpdateRequest",
    "WorkflowErrorCode",
    "WorkflowException",
    "WorkflowStateMachine",
    "JobRankerEngine",
    "JobRankingResult",
    "ApplicationPlanner",
    "WorkflowReferralManager",
    "DiscoveryScheduler",
    "AutonomousWorkflowOrchestrator",
    "WorkflowRepository",
    "WorkflowService",
    "default_workflow_service",
]
'''

FILES["app/api/autonomous_workflow.py"] = '''from typing import Optional, List, Dict, Any
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
'''

FILES["tests/test_phase7_autonomous_workflow.py"] = '''import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone
from fastapi.testclient import TestClient

from app.main import app
from app.memory.database import SessionLocal
from app.profile.models import UserProfile
from app.job_discovery.models import DiscoveredOpportunity
from app.application_pipeline.models import TrackedApplication
from app.autonomous_workflow.models import (
    AutonomousWorkflow,
    WorkflowStep,
    WorkflowApproval,
    WorkflowActionLog,
    WorkflowRetry,
)
from app.autonomous_workflow.schemas import (
    WorkflowStatus,
    WorkflowPriority,
    WorkflowStepStatus,
    ApprovalType,
    ApprovalStatus,
    UserActionType,
    PauseReason,
    WorkflowActionType,
    WorkflowCreateRequest,
    WorkflowApproveRequest,
    WorkflowRejectRequest,
    ReferralUpdateRequest,
)
from app.autonomous_workflow.errors import (
    WorkflowErrorCode,
    WorkflowException,
)
from app.autonomous_workflow.workflow_state import WorkflowStateMachine
from app.autonomous_workflow.job_ranker import JobRankerEngine
from app.autonomous_workflow.application_planner import ApplicationPlanner
from app.autonomous_workflow.referral_manager import WorkflowReferralManager
from app.autonomous_workflow.discovery_scheduler import DiscoveryScheduler
from app.autonomous_workflow.orchestrator import AutonomousWorkflowOrchestrator
from app.autonomous_workflow.service import default_workflow_service


class Phase7AutonomousWorkflowTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        cls.db = SessionLocal()

        # Clean tables
        cls.db.query(WorkflowRetry).delete()
        cls.db.query(WorkflowActionLog).delete()
        cls.db.query(WorkflowApproval).delete()
        cls.db.query(WorkflowStep).delete()
        cls.db.query(AutonomousWorkflow).delete()
        cls.db.query(TrackedApplication).delete()
        cls.db.query(DiscoveredOpportunity).delete()
        cls.db.commit()

        # Ensure user profile exists
        profile = cls.db.query(UserProfile).first()
        if not profile:
            profile = UserProfile(
                full_name="Alex Mercer",
                email="alex.mercer@example.com",
                phone="+1-555-0199",
                location="San Francisco, CA",
                linkedin_url="https://linkedin.com/in/alexmercer",
                github_url="https://github.com/alexmercer",
                portfolio_url="https://alexmercer.dev",
                skills=["Python", "FastAPI", "PostgreSQL", "Docker", "Distributed Systems"],
                target_roles=["Senior Backend Engineer", "Lead Python Developer"]
            )
            cls.db.add(profile)
            cls.db.commit()
            cls.db.refresh(profile)
        cls.profile = profile

    @classmethod
    def tearDownClass(cls):
        cls.db.close()

    def setUp(self):
        self.db.rollback()

    def _get_sample_greenhouse_html(self):
        return """
        <html>
        <head><title>Senior Platform Engineer at AutomationCorp</title></head>
        <body>
            <form id="application_form" action="/apply">
                <div class="field">
                    <label for="first_name">First Name *</label>
                    <input type="text" id="first_name" name="first_name" required />
                </div>
                <div class="field">
                    <label for="last_name">Last Name *</label>
                    <input type="text" id="last_name" name="last_name" required />
                </div>
                <div class="field">
                    <label for="email">Email *</label>
                    <input type="email" id="email" name="email" required />
                </div>
                <div class="field">
                    <label for="phone">Phone *</label>
                    <input type="tel" id="phone" name="phone" />
                </div>
                <div class="field">
                    <label for="job_application_answers_attributes_0_text_value">LinkedIn Profile</label>
                    <input type="text" id="job_application_answers_attributes_0_text_value" name="job_application[answers_attributes][0][text_value]" />
                </div>
                <button type="submit" id="submit_app">Submit Application</button>
            </form>
        </body>
        </html>
        """

    def test_01_create_workflow_manually(self):
        wf = default_workflow_service.create_workflow(
            company="Anthropic",
            role="Systems Engineer",
            source_url="https://boards.greenhouse.io/anthropic/jobs/101",
            source_platform="greenhouse",
            priority=WorkflowPriority.HIGH,
            match_score=88,
            db=self.db
        )
        self.assertIsNotNone(wf.id)
        self.assertEqual(wf.company, "Anthropic")
        self.assertEqual(wf.role, "Systems Engineer")
        self.assertEqual(wf.workflow_status, WorkflowStatus.CREATED)
        self.assertEqual(wf.workflow_priority, WorkflowPriority.HIGH)
        self.assertEqual(wf.match_score, 88)

    def test_02_create_workflow_from_opportunity(self):
        opp = DiscoveredOpportunity(
            title="Senior Platform Engineer",
            company="Stripe",
            description="Detailed job description for Senior Platform Engineer at Stripe.",
            location="Remote",
            provider="greenhouse",
            source_url="https://boards.greenhouse.io/stripe/jobs/202",
            match_score=92,
            recommendation="STRONGLY_RECOMMENDED",
            status="SAVED"
        )
        self.db.add(opp)
        self.db.commit()
        self.db.refresh(opp)

        wf = default_workflow_service.create_from_opportunity(
            opportunity_id=opp.id,
            priority=WorkflowPriority.URGENT,
            db=self.db
        )
        self.assertIsNotNone(wf.id)
        self.assertEqual(wf.opportunity_id, opp.id)
        self.assertEqual(wf.company, "Stripe")
        self.assertEqual(wf.role, "Senior Platform Engineer")
        self.assertEqual(wf.workflow_priority, WorkflowPriority.URGENT)

    def test_03_prevent_duplicate_workflow(self):
        with self.assertRaises(WorkflowException) as ctx:
            default_workflow_service.create_workflow(
                company="Anthropic",
                role="Systems Engineer",
                db=self.db
            )
        self.assertEqual(ctx.exception.code, WorkflowErrorCode.DUPLICATE_WORKFLOW)

    def test_04_valid_workflow_lifecycle_transition(self):
        # CREATED -> PLANNING
        self.assertTrue(WorkflowStateMachine.can_transition(WorkflowStatus.CREATED, WorkflowStatus.PLANNING))
        # PLANNING -> ASSETS_READY
        self.assertTrue(WorkflowStateMachine.can_transition(WorkflowStatus.PLANNING, WorkflowStatus.ASSETS_READY))
        # AUTOFILL_READY -> AUTOFILLING
        self.assertTrue(WorkflowStateMachine.can_transition(WorkflowStatus.AUTOFILL_READY, WorkflowStatus.AUTOFILLING))
        # SUBMISSION_PENDING -> APPLICATION_COMPLETED
        self.assertTrue(WorkflowStateMachine.can_transition(WorkflowStatus.SUBMISSION_PENDING, WorkflowStatus.APPLICATION_COMPLETED))
        # APPLICATION_COMPLETED -> CLOSED
        self.assertTrue(WorkflowStateMachine.can_transition(WorkflowStatus.APPLICATION_COMPLETED, WorkflowStatus.CLOSED))

    def test_05_invalid_workflow_transition_rejected(self):
        # Cannot jump from CREATED directly to APPLICATION_COMPLETED
        self.assertFalse(WorkflowStateMachine.can_transition(WorkflowStatus.CREATED, WorkflowStatus.APPLICATION_COMPLETED))
        with self.assertRaises(WorkflowException) as ctx:
            WorkflowStateMachine.validate_transition(WorkflowStatus.CREATED, WorkflowStatus.APPLICATION_COMPLETED)
        self.assertEqual(ctx.exception.code, WorkflowErrorCode.INVALID_WORKFLOW_TRANSITION)

    def test_06_start_workflow_and_idempotency(self):
        wf = default_workflow_service.create_workflow(
            company="OpenAI",
            role="Research Engineer",
            source_url="https://boards.greenhouse.io/openai/jobs/303",
            source_platform="greenhouse",
            priority=WorkflowPriority.HIGH,
            match_score=85,
            db=self.db
        )
        started_wf = default_workflow_service.start_workflow(workflow_id=wf.id, db=self.db)
        self.assertEqual(started_wf.workflow_status, WorkflowStatus.APPROVED)
        self.assertIsNotNone(started_wf.started_at)
        self.assertIsNotNone(started_wf.application_id)

        # Calling start again should be idempotent
        started_again = default_workflow_service.start_workflow(workflow_id=wf.id, db=self.db)
        self.assertEqual(started_again.workflow_status, WorkflowStatus.APPROVED)

    def test_07_approval_checkpoints(self):
        wf = default_workflow_service.create_workflow(
            company="Databricks",
            role="Data Engineer",
            priority=WorkflowPriority.MEDIUM,
            match_score=60,
            db=self.db
        )
        started_wf = default_workflow_service.start_workflow(workflow_id=wf.id, db=self.db)
        self.assertEqual(started_wf.workflow_status, WorkflowStatus.AWAITING_APPROVAL)

        # User approves checkpoint
        approved_wf = default_workflow_service.approve_checkpoint(
            workflow_id=wf.id,
            approval_type=ApprovalType.APPLICATION_APPROVAL,
            approved_by="alex",
            reason="Role fits goals",
            db=self.db
        )
        self.assertEqual(approved_wf.workflow_status, WorkflowStatus.APPROVED)

    def test_08_pause_and_resume(self):
        wf = default_workflow_service.create_workflow(
            company="Snowflake",
            role="Core Database Engineer",
            match_score=80,
            db=self.db
        )
        default_workflow_service.start_workflow(workflow_id=wf.id, db=self.db)

        # Pause
        paused_wf = default_workflow_service.pause_workflow(
            workflow_id=wf.id,
            reason=PauseReason.USER_PAUSED,
            db=self.db
        )
        self.assertEqual(paused_wf.workflow_status, WorkflowStatus.PAUSED)
        self.assertTrue(paused_wf.paused)
        self.assertEqual(paused_wf.pause_reason, PauseReason.USER_PAUSED.value)

        # Resume
        resumed_wf = default_workflow_service.resume_workflow(
            workflow_id=wf.id,
            db=self.db
        )
        self.assertEqual(resumed_wf.workflow_status, WorkflowStatus.PLANNING)
        self.assertFalse(resumed_wf.paused)

    def test_09_checkpoint_handling_and_safe_stops(self):
        wf_model = self.db.query(AutonomousWorkflow).first()
        # Test handle checkpoint method
        AutonomousWorkflowOrchestrator._handle_checkpoint(
            db=self.db,
            wf=wf_model,
            reason=PauseReason.CAPTCHA_DETECTED,
            action_type=UserActionType.SOLVE_CAPTCHA,
            instructions="Solve the CAPTCHA in browser"
        )
        self.assertEqual(wf_model.workflow_status, WorkflowStatus.AWAITING_USER_ACTION.value)
        self.assertTrue(wf_model.user_action_required)
        self.assertEqual(wf_model.pause_reason, PauseReason.CAPTCHA_DETECTED.value)

    @patch("app.core.brain.manager.BrainManager.generate")
    def test_10_asset_generation_integration(self, mock_ai):
        mock_ai.return_value = {
            "status": "success",
            "provider": "mock",
            "response": {
                "resume": {
                    "professional_summary": "Fullstack Engineer specializing in Python & React",
                    "relevant_skills": ["Python", "React", "PostgreSQL"],
                    "experience_bullets": ["Built scalable services"],
                    "achievement_bullets": ["Improved latency by 40%"]
                },
                "cover_letter": {
                    "salutation": "Dear Hiring Team,",
                    "opening": "I am excited to apply...",
                    "body_paragraphs": ["My background aligns well..."],
                    "closing": "Looking forward to speaking...",
                    "sign_off": "Sincerely,\\nAlex Mercer"
                },
                "recruiter_message": {
                    "subject": "Alex Mercer - Fullstack Engineer Application",
                    "message_body": "Hi there, I recently applied..."
                },
                "gap_analysis": {
                    "overall_score": 85,
                    "matching_skills": ["Python", "React"],
                    "missing_skills": [],
                    "recommendations": ["Highlight recent projects"]
                }
            }
        }
        wf = default_workflow_service.create_workflow(
            company="Figma",
            role="Fullstack Engineer",
            match_score=84,
            db=self.db
        )
        default_workflow_service.start_workflow(workflow_id=wf.id, db=self.db)
        res = default_workflow_service.generate_assets(workflow_id=wf.id, db=self.db)
        self.assertTrue(res.get("success"))
        updated_wf = default_workflow_service.get_workflow(wf.id, self.db)
        self.assertEqual(updated_wf.workflow_status, WorkflowStatus.ASSETS_READY)

    @patch("app.application_automation.browser.SafeHttpClient.get")
    def test_11_inspection_and_autofill_approval(self, mock_http):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = self._get_sample_greenhouse_html()
        mock_http.return_value = mock_resp

        wf = default_workflow_service.create_workflow(
            company="Airbnb",
            role="Backend Engineer",
            source_url="https://boards.greenhouse.io/airbnb/jobs/404",
            match_score=85,
            db=self.db
        )
        default_workflow_service.start_workflow(workflow_id=wf.id, db=self.db)
        default_workflow_service.generate_assets(workflow_id=wf.id, db=self.db)
        inspect_res = default_workflow_service.inspect_application(workflow_id=wf.id, db=self.db)
        self.assertIsNotNone(inspect_res)

        # Autofill without approval should raise error
        with self.assertRaises(WorkflowException) as ctx:
            default_workflow_service.autofill_approved_fields(workflow_id=wf.id, db=self.db)
        self.assertEqual(ctx.exception.code, WorkflowErrorCode.APPROVAL_REQUIRED)

        # Approve autofill
        default_workflow_service.approve_checkpoint(
            workflow_id=wf.id,
            approval_type=ApprovalType.AUTOFILL_APPROVAL,
            db=self.db
        )
        # Now autofill succeeds
        fill_res = default_workflow_service.autofill_approved_fields(workflow_id=wf.id, db=self.db)
        self.assertIsNotNone(fill_res)
        updated_wf = default_workflow_service.get_workflow(wf.id, self.db)
        self.assertEqual(updated_wf.workflow_status, WorkflowStatus.SUBMISSION_PENDING)

    def test_12_manual_submission_confirmation(self):
        wf = default_workflow_service.create_workflow(
            company="Vercel",
            role="Infrastructure Engineer",
            match_score=89,
            db=self.db
        )
        default_workflow_service.start_workflow(workflow_id=wf.id, db=self.db)
        confirmed_wf = default_workflow_service.confirm_manual_submission(
            workflow_id=wf.id,
            notes="Submitted manually on Vercel careers portal",
            db=self.db
        )
        self.assertEqual(confirmed_wf.workflow_status, WorkflowStatus.APPLICATION_COMPLETED)
        self.assertIsNotNone(confirmed_wf.completed_at)

        # Tracked application should be APPLIED
        tracked_app = self.db.query(TrackedApplication).filter(TrackedApplication.id == confirmed_wf.application_id).first()
        self.assertIsNotNone(tracked_app)
        self.assertEqual(tracked_app.status, "APPLIED")

    def test_13_retry_policy_and_limits(self):
        wf = default_workflow_service.create_workflow(
            company="Linear",
            role="Frontend Engineer",
            match_score=75,
            db=self.db
        )
        # Attempt retries
        default_workflow_service.retry_workflow(wf.id, self.db)
        default_workflow_service.retry_workflow(wf.id, self.db)
        default_workflow_service.retry_workflow(wf.id, self.db)

        # 4th retry should hit limit
        with self.assertRaises(WorkflowException) as ctx:
            default_workflow_service.retry_workflow(wf.id, self.db)
        self.assertEqual(ctx.exception.code, WorkflowErrorCode.RETRY_LIMIT_REACHED)

    def test_14_discovery_scheduler_and_job_ranker(self):
        # Create un-queued opportunities
        opp1 = DiscoveredOpportunity(
            title="Staff Engineer",
            company="Netflix",
            description="Staff Engineer distributed systems at Netflix.",
            provider="lever",
            source_url="https://jobs.lever.co/netflix/505",
            match_score=95,
            recommendation="STRONGLY_RECOMMENDED",
            status="DISCOVERED"
        )
        opp2 = DiscoveredOpportunity(
            title="Junior QA",
            company="RandomCorp",
            description="Junior QA manual testing at RandomCorp.",
            provider="lever",
            source_url="https://jobs.lever.co/random/506",
            match_score=40,
            recommendation="LOW_FIT",
            status="DISCOVERED"
        )
        self.db.add_all([opp1, opp2])
        self.db.commit()

        run_res = DiscoveryScheduler.run_discovery_cycle(db=self.db, min_score_threshold=70)
        self.assertTrue(run_res.success)
        self.assertGreaterEqual(run_res.workflows_created, 1)

    def test_15_api_queue_and_dashboard(self):
        resp = self.client.get("/workflow/queue")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("total", data)
        self.assertIn("urgent", data)
        self.assertIn("ready_for_approval", data)

        dash_resp = self.client.get("/workflow/dashboard")
        self.assertEqual(dash_resp.status_code, 200)
        dash_data = dash_resp.json()
        self.assertIn("total_active_workflows", dash_data)
        self.assertIn("top_companies", dash_data)

    def test_16_referral_tracking_integration(self):
        wf = default_workflow_service.create_workflow(
            company="Notion",
            role="Product Engineer",
            match_score=88,
            db=self.db
        )
        default_workflow_service.start_workflow(workflow_id=wf.id, db=self.db)
        ref_update = ReferralUpdateRequest(
            referral_contact_name="Sarah Connor",
            referral_contact_identifier="sarah@notion.so",
            referral_status="REQUESTED",
            referral_notes="Sent intro email via alumni network"
        )
        res = default_workflow_service.update_referral(
            workflow_id=wf.id,
            referral_data=ref_update,
            db=self.db
        )
        self.assertEqual(res.get("referral_status"), "REQUESTED")
        self.assertEqual(res.get("referral_contact_name"), "Sarah Connor")

    def test_17_action_audit_log(self):
        wf = self.db.query(AutonomousWorkflow).first()
        logs = default_workflow_service.get_actions(wf.id, self.db)
        self.assertGreater(logs.total, 0)
        self.assertIsNotNone(logs.logs[0].action_type)

    def test_18_terminal_state_protection(self):
        wf = default_workflow_service.create_workflow(
            company="ClosedCorp",
            role="Engineer",
            match_score=50,
            db=self.db
        )
        cancelled = default_workflow_service.cancel_workflow(wf.id, reason="No longer interested", db=self.db)
        self.assertEqual(cancelled.workflow_status, WorkflowStatus.CANCELLED)

        # Cannot pause a cancelled workflow
        with self.assertRaises(WorkflowException) as ctx:
            default_workflow_service.pause_workflow(wf.id, db=self.db)
        self.assertEqual(ctx.exception.code, WorkflowErrorCode.INVALID_WORKFLOW_TRANSITION)


if __name__ == "__main__":
    unittest.main()
'''

for rel_path, content in FILES.items():
    full_path = os.path.join(BASE_DIR, rel_path.replace("/", os.sep))
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content)
        f.flush()
        os.fsync(f.fileno())
    print(f"WROTE: {rel_path} ({len(content)} bytes)")
