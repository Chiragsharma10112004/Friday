import logging
from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy.orm import Session

from app.autonomous_workflow.models import AutonomousWorkflow, WorkflowStep, WorkflowApproval, WorkflowActionLog
from app.autonomous_workflow.schemas import (
    WorkflowStatus,
    WorkflowPriority,
    ApprovalType,
    ApprovalStatus,
    PauseReason,
    WorkflowResponse,
    WorkflowListResponse,
    WorkflowStepListResponse,
    WorkflowApprovalListResponse,
    WorkflowActionLogListResponse,
    WorkflowPlanResponse,
    WorkflowQueueResponse,
    WorkflowDashboardResponse,
    WorkflowNextActionResponse,
    DiscoveryRunResponse,
    ReferralUpdateRequest,
)
from app.autonomous_workflow.orchestrator import AutonomousWorkflowOrchestrator
from app.autonomous_workflow.repository import WorkflowRepository
from app.autonomous_workflow.application_planner import ApplicationPlanner
from app.autonomous_workflow.referral_manager import WorkflowReferralManager
from app.autonomous_workflow.discovery_scheduler import DiscoveryScheduler

logger = logging.getLogger("friday.autonomous_workflow.service")


class WorkflowService:
    """
    High-level service layer exposing autonomous workflow capabilities to REST API and agents.
    """

    @classmethod
    def create_workflow(
        cls,
        company: str,
        role: str,
        source_url: Optional[str] = None,
        source_platform: Optional[str] = None,
        priority: WorkflowPriority = WorkflowPriority.MEDIUM,
        opportunity_id: Optional[int] = None,
        application_id: Optional[int] = None,
        job_description: Optional[str] = None,
        match_score: Optional[int] = None,
        db: Session = None
    ) -> WorkflowResponse:
        wf = AutonomousWorkflowOrchestrator.create_workflow(
            db=db,
            company=company,
            role=role,
            source_url=source_url,
            source_platform=source_platform,
            priority=priority,
            opportunity_id=opportunity_id,
            application_id=application_id,
            job_description=job_description,
            match_score=match_score
        )
        return wf.to_schema()

    @classmethod
    def create_from_opportunity(
        cls,
        opportunity_id: int,
        priority: Optional[WorkflowPriority] = None,
        db: Session = None
    ) -> WorkflowResponse:
        wf = AutonomousWorkflowOrchestrator.create_from_opportunity(
            db=db,
            opportunity_id=opportunity_id,
            priority=priority
        )
        return wf.to_schema()

    @classmethod
    def start_workflow(
        cls,
        workflow_id: int,
        db: Session
    ) -> WorkflowResponse:
        wf = AutonomousWorkflowOrchestrator.start_workflow(db=db, workflow_id=workflow_id)
        return wf.to_schema()

    @classmethod
    def pause_workflow(
        cls,
        workflow_id: int,
        reason: PauseReason = PauseReason.USER_PAUSED,
        db: Session = None
    ) -> WorkflowResponse:
        wf = AutonomousWorkflowOrchestrator.pause_workflow(db=db, workflow_id=workflow_id, reason=reason)
        return wf.to_schema()

    @classmethod
    def resume_workflow(
        cls,
        workflow_id: int,
        db: Session
    ) -> WorkflowResponse:
        wf = AutonomousWorkflowOrchestrator.resume_workflow(db=db, workflow_id=workflow_id)
        return wf.to_schema()

    @classmethod
    def retry_workflow(
        cls,
        workflow_id: int,
        db: Session
    ) -> WorkflowResponse:
        wf = AutonomousWorkflowOrchestrator.retry_workflow(db=db, workflow_id=workflow_id)
        return wf.to_schema()

    @classmethod
    def cancel_workflow(
        cls,
        workflow_id: int,
        reason: str = "User cancelled",
        db: Session = None
    ) -> WorkflowResponse:
        wf = AutonomousWorkflowOrchestrator.cancel_workflow(db=db, workflow_id=workflow_id, reason=reason)
        return wf.to_schema()

    @classmethod
    def approve_checkpoint(
        cls,
        workflow_id: int,
        approval_type: Optional[ApprovalType] = None,
        approved_by: str = "user",
        reason: Optional[str] = None,
        db: Session = None
    ) -> WorkflowResponse:
        wf = AutonomousWorkflowOrchestrator.approve_checkpoint(
            db=db,
            workflow_id=workflow_id,
            approval_type=approval_type,
            approved_by=approved_by,
            reason=reason
        )
        return wf.to_schema()

    @classmethod
    def reject_checkpoint(
        cls,
        workflow_id: int,
        approval_type: Optional[ApprovalType] = None,
        rejected_by: str = "user",
        reason: str = "Rejected by user",
        db: Session = None
    ) -> WorkflowResponse:
        wf = AutonomousWorkflowOrchestrator.reject_checkpoint(
            db=db,
            workflow_id=workflow_id,
            approval_type=approval_type,
            rejected_by=rejected_by,
            reason=reason
        )
        return wf.to_schema()

    @classmethod
    def get_workflow(
        cls,
        workflow_id: int,
        db: Session
    ) -> WorkflowResponse:
        wf = WorkflowRepository.get_workflow(db, workflow_id)
        return wf.to_schema()

    @classmethod
    def list_workflows(
        cls,
        priority: Optional[WorkflowPriority] = None,
        status: Optional[WorkflowStatus] = None,
        company: Optional[str] = None,
        min_match_score: Optional[int] = None,
        user_action_required: Optional[bool] = None,
        skip: int = 0,
        limit: int = 50,
        db: Session = None
    ) -> WorkflowListResponse:
        items, total = WorkflowRepository.list_workflows(
            db=db,
            priority=priority,
            status=status,
            company=company,
            min_match_score=min_match_score,
            user_action_required=user_action_required,
            skip=skip,
            limit=limit
        )
        return WorkflowListResponse(total=total, items=[w.to_schema() for w in items])

    @classmethod
    def get_plan(
        cls,
        workflow_id: int,
        db: Session
    ) -> WorkflowPlanResponse:
        wf = WorkflowRepository.get_workflow(db, workflow_id)
        return ApplicationPlanner.create_execution_plan(workflow=wf)

    @classmethod
    def get_steps(
        cls,
        workflow_id: int,
        db: Session
    ) -> WorkflowStepListResponse:
        steps = WorkflowRepository.get_steps(db, workflow_id)
        return WorkflowStepListResponse(total=len(steps), steps=[s.to_schema() for s in steps])

    @classmethod
    def get_actions(
        cls,
        workflow_id: int,
        db: Session
    ) -> WorkflowActionLogListResponse:
        logs = WorkflowRepository.get_action_logs(db, workflow_id)
        return WorkflowActionLogListResponse(total=len(logs), logs=[l.to_schema() for l in logs])

    @classmethod
    def get_approvals(
        cls,
        workflow_id: Optional[int] = None,
        status: Optional[ApprovalStatus] = None,
        db: Session = None
    ) -> WorkflowApprovalListResponse:
        approvals = WorkflowRepository.list_approvals(db, workflow_id=workflow_id, status=status)
        return WorkflowApprovalListResponse(total=len(approvals), approvals=[a.to_schema() for a in approvals])

    @classmethod
    def get_queue(cls, db: Session) -> WorkflowQueueResponse:
        return WorkflowRepository.get_queue_summary(db)

    @classmethod
    def get_dashboard(cls, db: Session) -> WorkflowDashboardResponse:
        return WorkflowRepository.get_dashboard_summary(db)

    @classmethod
    def get_next_action(cls, workflow_id: int, db: Session) -> WorkflowNextActionResponse:
        return AutonomousWorkflowOrchestrator.get_next_action(db, workflow_id)

    @classmethod
    def generate_assets(cls, workflow_id: int, db: Session) -> Dict[str, Any]:
        return AutonomousWorkflowOrchestrator.generate_assets(db, workflow_id)

    @classmethod
    def inspect_application(cls, workflow_id: int, db: Session) -> Dict[str, Any]:
        return AutonomousWorkflowOrchestrator.inspect_application(db, workflow_id)

    @classmethod
    def autofill_approved_fields(
        cls,
        workflow_id: int,
        approved_field_ids: Optional[List[str]] = None,
        db: Session = None
    ) -> Dict[str, Any]:
        return AutonomousWorkflowOrchestrator.autofill_approved_fields(
            db=db,
            workflow_id=workflow_id,
            approved_field_ids=approved_field_ids
        )

    @classmethod
    def update_referral(
        cls,
        workflow_id: int,
        referral_data: ReferralUpdateRequest,
        db: Session
    ) -> Dict[str, Any]:
        wf = WorkflowRepository.get_workflow(db, workflow_id)
        return WorkflowReferralManager.update_referral_state(
            db=db,
            workflow=wf,
            referral_contact_name=referral_data.referral_contact_name,
            referral_contact_identifier=referral_data.referral_contact_identifier,
            referral_status=referral_data.referral_status,
            referral_notes=referral_data.referral_notes
        )

    @classmethod
    def confirm_manual_submission(
        cls,
        workflow_id: int,
        notes: Optional[str] = None,
        db: Session = None
    ) -> WorkflowResponse:
        wf = AutonomousWorkflowOrchestrator.confirm_manual_submission(
            db=db,
            workflow_id=workflow_id,
            submission_notes=notes
        )
        return wf.to_schema()

    @classmethod
    def run_discovery(
        cls,
        min_score_threshold: int = 70,
        db: Session = None
    ) -> DiscoveryRunResponse:
        return DiscoveryScheduler.run_discovery_cycle(
            db=db,
            min_score_threshold=min_score_threshold
        )


default_workflow_service = WorkflowService()
