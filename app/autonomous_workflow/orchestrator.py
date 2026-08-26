import json
import logging
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy.orm import Session

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
    WorkflowActionType,
    UserActionType,
    PauseReason,
    WorkflowNextActionResponse,
)
from app.autonomous_workflow.errors import WorkflowErrorCode, WorkflowException
from app.autonomous_workflow.workflow_state import WorkflowStateMachine
from app.autonomous_workflow.job_ranker import JobRankerEngine
from app.autonomous_workflow.application_planner import ApplicationPlanner
from app.autonomous_workflow.referral_manager import WorkflowReferralManager
from app.autonomous_workflow.repository import WorkflowRepository

# Cross-phase integrations
from app.profile.models import UserProfile
from app.job_discovery.models import DiscoveredOpportunity
from app.application_pipeline.models import TrackedApplication
from app.application_pipeline.schemas import (
    ApplicationStatus,
    ApplicationPriority as PipelinePriority,
    CreateApplicationRequest,
    UpdateApplicationRequest,
)
from app.application_pipeline.service import ApplicationPipelineService
from app.application_assets.service import AssetGenerationService
from app.application_assets.schemas import ApplicationAssetRequest
from app.application_automation.service import ApplicationAutomationService
from app.application_automation.schemas import InspectApplicationRequest, FillApprovedFieldsRequest

logger = logging.getLogger("friday.autonomous_workflow.orchestrator")


class AutonomousWorkflowOrchestrator:
    """
    Central orchestrator coordinating discovery, matching, pipeline tracking,
    asset synthesis, form inspection, safe autofill, and manual human checkpoints.
    """

    MAX_RETRIES = 3

    @classmethod
    def create_workflow(
        cls,
        db: Session,
        company: str,
        role: str,
        source_url: Optional[str] = None,
        source_platform: Optional[str] = None,
        priority: WorkflowPriority = WorkflowPriority.MEDIUM,
        profile_id: Optional[int] = None,
        opportunity_id: Optional[int] = None,
        application_id: Optional[int] = None,
        job_description: Optional[str] = None,
        match_score: Optional[int] = None,
    ) -> AutonomousWorkflow:
        # Check duplicate
        existing = WorkflowRepository.check_duplicate_workflow(
            db=db,
            company=company,
            role=role,
            opportunity_id=opportunity_id,
            application_id=application_id
        )
        if existing:
            raise WorkflowException(
                code=WorkflowErrorCode.DUPLICATE_WORKFLOW,
                message=f"An active workflow already exists for {role} at {company} (ID: {existing.id}).",
                workflow_id=existing.id
            )

        if not profile_id:
            prof = db.query(UserProfile).first()
            if prof:
                profile_id = prof.id

        # If opportunity_id provided, sync metadata
        if opportunity_id:
            opp = db.query(DiscoveredOpportunity).filter(DiscoveredOpportunity.id == opportunity_id).first()
            if opp:
                company = opp.company
                role = opp.title
                source_url = opp.source_url or opp.application_url
                source_platform = opp.provider
                match_score = opp.match_score

        # Initial ranking
        ranking = JobRankerEngine.rank_job(
            match_score=match_score,
            missing_skills_count=0,
            has_referral=False
        )
        effective_priority = priority or ranking.priority

        wf = WorkflowRepository.create_workflow(
            db=db,
            company=company,
            role=role,
            source_url=source_url,
            source_platform=source_platform,
            priority=effective_priority,
            profile_id=profile_id,
            opportunity_id=opportunity_id,
            application_id=application_id,
            match_score=match_score or ranking.final_score,
            initial_status=WorkflowStatus.CREATED,
            metadata={"job_description": job_description} if job_description else None
        )

        return wf

    @classmethod
    def create_from_opportunity(
        cls,
        db: Session,
        opportunity_id: int,
        priority: Optional[WorkflowPriority] = None
    ) -> AutonomousWorkflow:
        opp = db.query(DiscoveredOpportunity).filter(DiscoveredOpportunity.id == opportunity_id).first()
        if not opp:
            raise WorkflowException(
                code=WorkflowErrorCode.OPPORTUNITY_NOT_FOUND,
                message=f"Opportunity with ID {opportunity_id} not found.",
            )

        # Check duplicate
        existing = WorkflowRepository.get_workflow_by_opportunity(db, opportunity_id)
        if existing and existing.workflow_status not in (WorkflowStatus.CANCELLED.value, WorkflowStatus.CLOSED.value):
            raise WorkflowException(
                code=WorkflowErrorCode.DUPLICATE_WORKFLOW,
                message=f"Workflow already exists for opportunity {opportunity_id} (ID: {existing.id}).",
                workflow_id=existing.id
            )

        wf = cls.create_workflow(
            db=db,
            company=opp.company,
            role=opp.title,
            source_url=opp.source_url or opp.application_url,
            source_platform=opp.provider,
            priority=priority or (WorkflowPriority.HIGH if (opp.match_score or 0) >= 80 else WorkflowPriority.MEDIUM),
            opportunity_id=opp.id,
            match_score=opp.match_score,
        )

        WorkflowRepository.create_action_log(
            db=db,
            workflow_id=wf.id,
            action_type=WorkflowActionType.OPPORTUNITY_LINKED,
            description=f"Linked to discovered opportunity #{opp.id} ({opp.company})."
        )
        return wf

    @classmethod
    def start_workflow(
        cls,
        db: Session,
        workflow_id: int
    ) -> AutonomousWorkflow:
        wf = WorkflowRepository.get_workflow(db, workflow_id)
        current_status = WorkflowStatus(wf.workflow_status)

        # Idempotency check: if already running or past started state, do not duplicate
        if current_status not in (WorkflowStatus.CREATED, WorkflowStatus.DISCOVERED, WorkflowStatus.QUEUED_FOR_REVIEW):
            return wf

        now = datetime.now(timezone.utc)
        wf.started_at = now

        # Transition to PLANNING or APPROVED
        next_status = WorkflowStatus.APPROVED if (wf.match_score or 0) >= 70 else WorkflowStatus.AWAITING_APPROVAL
        WorkflowStateMachine.validate_transition(current_status, next_status, workflow_id=wf.id)

        wf.workflow_status = next_status.value
        wf.current_step = "PLANNING"
        wf.next_action = "Review application plan and generate tailored assets"
        wf.updated_at = now

        # Ensure Phase 6 TrackedApplication exists
        if not wf.application_id:
            try:
                create_req = CreateApplicationRequest(
                    company=wf.company,
                    role=wf.role,
                    source_url=wf.source_url,
                    source_platform=wf.source_platform,
                    priority=PipelinePriority.HIGH if wf.workflow_priority == WorkflowPriority.HIGH.value else PipelinePriority.MEDIUM,
                    match_score=wf.match_score,
                    opportunity_id=wf.opportunity_id,
                )
                tracked_app = ApplicationPipelineService.create_application(
                    request=create_req,
                    db=db
                )
                wf.application_id = tracked_app.id
                WorkflowRepository.create_action_log(
                    db=db,
                    workflow_id=wf.id,
                    action_type=WorkflowActionType.APPLICATION_CREATED,
                    description=f"Created tracked application #{tracked_app.id} in application pipeline."
                )
            except Exception as e:
                logger.warning(f"Could not automatically create TrackedApplication for workflow {wf.id}: {e}")

        # Create execution plan steps in DB
        WorkflowRepository.create_step(db, wf.id, "GENERATE_RESUME", 1, WorkflowStepStatus.PENDING)
        WorkflowRepository.create_step(db, wf.id, "GENERATE_COVER_LETTER", 2, WorkflowStepStatus.PENDING)
        WorkflowRepository.create_step(db, wf.id, "INSPECT_APPLICATION", 3, WorkflowStepStatus.PENDING)
        WorkflowRepository.create_step(db, wf.id, "AUTOFILL_SAFE_FIELDS", 4, WorkflowStepStatus.PENDING)
        WorkflowRepository.create_step(db, wf.id, "MANUAL_SUBMISSION", 5, WorkflowStepStatus.PENDING)

        WorkflowRepository.create_action_log(
            db=db,
            workflow_id=wf.id,
            action_type=WorkflowActionType.APPLICATION_APPROVED if next_status == WorkflowStatus.APPROVED else WorkflowActionType.APPLICATION_APPROVAL_REQUESTED,
            description=f"Workflow started. Status advanced to '{next_status.value}'."
        )
        db.commit()
        db.refresh(wf)
        return wf

    @classmethod
    def pause_workflow(
        cls,
        db: Session,
        workflow_id: int,
        reason: PauseReason = PauseReason.USER_PAUSED
    ) -> AutonomousWorkflow:
        wf = WorkflowRepository.get_workflow(db, workflow_id)
        current_status = WorkflowStatus(wf.workflow_status)

        if current_status in WorkflowStateMachine.TERMINAL_STATES:
            raise WorkflowException(
                code=WorkflowErrorCode.INVALID_WORKFLOW_TRANSITION,
                message=f"Cannot pause workflow in terminal state '{current_status.value}'.",
                workflow_id=wf.id
            )

        now = datetime.now(timezone.utc)
        wf.workflow_status = WorkflowStatus.PAUSED.value
        wf.paused = True
        wf.pause_reason = reason.value
        wf.paused_at = now
        wf.updated_at = now

        WorkflowRepository.create_action_log(
            db=db,
            workflow_id=wf.id,
            action_type=WorkflowActionType.WORKFLOW_PAUSED,
            description=f"Workflow paused. Reason: {reason.value}."
        )
        db.commit()
        db.refresh(wf)
        return wf

    @classmethod
    def resume_workflow(
        cls,
        db: Session,
        workflow_id: int
    ) -> AutonomousWorkflow:
        wf = WorkflowRepository.get_workflow(db, workflow_id)
        current_status = WorkflowStatus(wf.workflow_status)

        if current_status in WorkflowStateMachine.TERMINAL_STATES:
            raise WorkflowException(
                code=WorkflowErrorCode.INVALID_WORKFLOW_TRANSITION,
                message=f"Cannot resume terminal workflow '{current_status.value}'.",
                workflow_id=wf.id
            )

        now = datetime.now(timezone.utc)
        wf.paused = False
        wf.pause_reason = None
        wf.user_action_required = False
        wf.updated_at = now

        # Determine target resume state based on current step
        if wf.current_step == "AUTOFILL_READY":
            resumed_status = WorkflowStatus.AUTOFILL_READY
        elif wf.current_step == "ASSETS_READY":
            resumed_status = WorkflowStatus.ASSETS_READY
        elif wf.current_step == "INSPECTED":
            resumed_status = WorkflowStatus.APPLICATION_INSPECTED
        elif wf.current_step == "SUBMISSION_PENDING":
            resumed_status = WorkflowStatus.SUBMISSION_PENDING
        else:
            resumed_status = WorkflowStatus.PLANNING

        wf.workflow_status = resumed_status.value
        wf.next_action = f"Continue workflow from step {wf.current_step or 'PLANNING'}"

        WorkflowRepository.create_action_log(
            db=db,
            workflow_id=wf.id,
            action_type=WorkflowActionType.WORKFLOW_RESUMED,
            description=f"Workflow resumed to '{resumed_status.value}'."
        )
        db.commit()
        db.refresh(wf)
        return wf

    @classmethod
    def retry_workflow(
        cls,
        db: Session,
        workflow_id: int
    ) -> AutonomousWorkflow:
        wf = WorkflowRepository.get_workflow(db, workflow_id)
        if wf.retry_count >= cls.MAX_RETRIES:
            raise WorkflowException(
                code=WorkflowErrorCode.RETRY_LIMIT_REACHED,
                message=f"Maximum retries ({cls.MAX_RETRIES}) reached for workflow {workflow_id}.",
                workflow_id=wf.id
            )

        wf.retry_count += 1
        wf.workflow_status = WorkflowStatus.PLANNING.value
        wf.last_error = None
        wf.paused = False
        wf.pause_reason = None
        wf.updated_at = datetime.now(timezone.utc)

        WorkflowRepository.create_action_log(
            db=db,
            workflow_id=wf.id,
            action_type=WorkflowActionType.RETRY_ATTEMPTED,
            description=f"Retry attempt #{wf.retry_count} initiated."
        )
        db.commit()
        db.refresh(wf)
        return wf

    @classmethod
    def cancel_workflow(
        cls,
        db: Session,
        workflow_id: int,
        reason: str = "User cancelled"
    ) -> AutonomousWorkflow:
        wf = WorkflowRepository.get_workflow(db, workflow_id)
        current_status = WorkflowStatus(wf.workflow_status)

        if current_status == WorkflowStatus.CLOSED:
            raise WorkflowException(
                code=WorkflowErrorCode.INVALID_WORKFLOW_TRANSITION,
                message="Cannot cancel a closed workflow.",
                workflow_id=wf.id
            )

        wf.workflow_status = WorkflowStatus.CANCELLED.value
        wf.next_action = "Workflow cancelled"
        wf.updated_at = datetime.now(timezone.utc)

        WorkflowRepository.create_action_log(
            db=db,
            workflow_id=wf.id,
            action_type=WorkflowActionType.APPLICATION_REJECTED,
            description=f"Workflow cancelled: {reason}."
        )
        db.commit()
        db.refresh(wf)
        return wf

    @classmethod
    def approve_checkpoint(
        cls,
        db: Session,
        workflow_id: int,
        approval_type: Optional[ApprovalType] = None,
        approved_by: str = "user",
        reason: Optional[str] = None
    ) -> AutonomousWorkflow:
        wf = WorkflowRepository.get_workflow(db, workflow_id)
        approvals = WorkflowRepository.list_approvals(db, workflow_id=wf.id, status=ApprovalStatus.PENDING)

        now = datetime.now(timezone.utc)
        for appr in approvals:
            if not approval_type or appr.approval_type == approval_type.value:
                appr.status = ApprovalStatus.APPROVED.value
                appr.approved_at = now
                appr.approved_by = approved_by
                appr.reason = reason or "Approved by user"
                appr.updated_at = now

        wf.approval_required = False
        wf.user_action_required = False

        # Advance state depending on approval context
        current_status = WorkflowStatus(wf.workflow_status)
        if current_status in (WorkflowStatus.AWAITING_APPROVAL, WorkflowStatus.QUEUED_FOR_REVIEW):
            wf.workflow_status = WorkflowStatus.APPROVED.value
        elif current_status == WorkflowStatus.AUTOFILL_READY:
            wf.workflow_status = WorkflowStatus.AUTOFILLING.value

        WorkflowRepository.create_action_log(
            db=db,
            workflow_id=wf.id,
            action_type=WorkflowActionType.APPLICATION_APPROVED,
            description=f"Approval granted by {approved_by}: {reason or 'Approved'}."
        )
        db.commit()
        db.refresh(wf)
        return wf

    @classmethod
    def reject_checkpoint(
        cls,
        db: Session,
        workflow_id: int,
        approval_type: Optional[ApprovalType] = None,
        rejected_by: str = "user",
        reason: str = "Rejected by user"
    ) -> AutonomousWorkflow:
        wf = WorkflowRepository.get_workflow(db, workflow_id)
        approvals = WorkflowRepository.list_approvals(db, workflow_id=wf.id, status=ApprovalStatus.PENDING)

        now = datetime.now(timezone.utc)
        for appr in approvals:
            if not approval_type or appr.approval_type == approval_type.value:
                appr.status = ApprovalStatus.REJECTED.value
                appr.rejected_at = now
                appr.reason = reason
                appr.updated_at = now

        wf.approval_required = False
        wf.workflow_status = WorkflowStatus.PAUSED.value
        wf.pause_reason = PauseReason.USER_PAUSED.value
        wf.paused = True
        wf.paused_at = now

        WorkflowRepository.create_action_log(
            db=db,
            workflow_id=wf.id,
            action_type=WorkflowActionType.APPLICATION_REJECTED,
            description=f"Approval rejected by {rejected_by}: {reason}."
        )
        db.commit()
        db.refresh(wf)
        return wf

    @classmethod
    def generate_assets(
        cls,
        db: Session,
        workflow_id: int
    ) -> Dict[str, Any]:
        wf = WorkflowRepository.get_workflow(db, workflow_id)
        wf.workflow_status = WorkflowStatus.ASSETS_GENERATING.value
        wf.current_step = "ASSETS_GENERATING"
        db.commit()

        # Call Phase 3 AssetGenerationService
        try:
            req = ApplicationAssetRequest(
                company=wf.company,
                role=wf.role,
                job_description=f"Position: {wf.role} at {wf.company}. Requirements: Python, Backend, Distributed Systems.",
                application_id=wf.application_id
            )
            bundle = AssetGenerationService.generate_assets(req, db)

            wf.workflow_status = WorkflowStatus.ASSETS_READY.value
            wf.current_step = "ASSETS_READY"
            wf.next_action = "Inspect target application form and prepare autofill"

            # Update step
            steps = WorkflowRepository.get_steps(db, wf.id)
            for s in steps:
                if s.step_name in ("GENERATE_RESUME", "GENERATE_COVER_LETTER"):
                    WorkflowRepository.update_step(db, s.id, status=WorkflowStepStatus.COMPLETED)

            WorkflowRepository.create_action_log(
                db=db,
                workflow_id=wf.id,
                action_type=WorkflowActionType.ASSET_GENERATION_COMPLETED,
                description="Tailored resume and cover letter generated successfully."
            )
            db.commit()
            db.refresh(wf)
            bundle_dict = bundle.model_dump() if hasattr(bundle, "model_dump") else (bundle.dict() if hasattr(bundle, "dict") else {})
            return {"success": True, "bundle": bundle_dict}
        except Exception as e:
            wf.workflow_status = WorkflowStatus.FAILED.value
            wf.last_error = str(e)
            WorkflowRepository.create_action_log(
                db=db,
                workflow_id=wf.id,
                action_type=WorkflowActionType.WORKFLOW_FAILED,
                description=f"Asset generation failed: {e}",
                status="FAILED"
            )
            db.commit()
            db.refresh(wf)
            raise WorkflowException(
                code=WorkflowErrorCode.ASSET_GENERATION_FAILED,
                message=f"Failed to generate application assets: {e}",
                workflow_id=wf.id
            )

    @classmethod
    def inspect_application(
        cls,
        db: Session,
        workflow_id: int
    ) -> Dict[str, Any]:
        wf = WorkflowRepository.get_workflow(db, workflow_id)
        wf.workflow_status = WorkflowStatus.APPLICATION_INSPECTING.value
        wf.current_step = "APPLICATION_INSPECTING"
        db.commit()

        try:
            req = InspectApplicationRequest(
                application_url=wf.source_url or f"https://boards.greenhouse.io/{wf.company.lower()}/jobs/101",
                application_id=wf.application_id
            )
            inspect_res = ApplicationAutomationService.inspect_form(req, db)

            status_str = inspect_res.status.value if hasattr(inspect_res.status, "value") else str(inspect_res.status)

            # Handle Checkpoints safely
            if status_str in ("AUTH_REQUIRED", "AUTHENTICATION_REQUIRED"):
                cls._handle_checkpoint(db, wf, PauseReason.AUTHENTICATION_REQUIRED, UserActionType.SIGN_IN, "Please sign into the company career portal in your browser.")
            elif status_str == "ACCOUNT_CREATION_REQUIRED":
                cls._handle_checkpoint(db, wf, PauseReason.ACCOUNT_CREATION_REQUIRED, UserActionType.CREATE_ACCOUNT, "Please create an account on the company career portal.")
            elif status_str == "CAPTCHA_DETECTED":
                cls._handle_checkpoint(db, wf, PauseReason.CAPTCHA_DETECTED, UserActionType.SOLVE_CAPTCHA, "CAPTCHA challenge detected. Please solve the challenge manually.")
            elif status_str == "EMAIL_VERIFICATION_REQUIRED":
                cls._handle_checkpoint(db, wf, PauseReason.EMAIL_VERIFICATION_REQUIRED, UserActionType.VERIFY_EMAIL, "Email verification or OTP required. Please verify in your browser.")
            elif inspect_res.page_type == "JOB_DETAILS":
                cls._handle_checkpoint(db, wf, PauseReason.USER_ACTION_REQUIRED, UserActionType.SUBMIT_APPLICATION_MANUALLY, "Job description page. Click 'Apply' to reach application form.")
            else:
                # PREVIEW_READY / Form Inspected
                wf.workflow_status = WorkflowStatus.AUTOFILL_READY.value
                wf.current_step = "AUTOFILL_READY"
                wf.next_action = "Review and approve fields for safe autofill"
                wf.approval_required = True
                WorkflowRepository.create_approval(db, wf.id, ApprovalType.AUTOFILL_APPROVAL)

            # Update step
            steps = WorkflowRepository.get_steps(db, wf.id)
            for s in steps:
                if s.step_name == "INSPECT_APPLICATION":
                    WorkflowRepository.update_step(db, s.id, status=WorkflowStepStatus.COMPLETED)

            meta = json.loads(wf.metadata_json) if wf.metadata_json else {}
            if getattr(inspect_res, "session_id", None):
                meta["session_id"] = inspect_res.session_id
                wf.metadata_json = json.dumps(meta)

            WorkflowRepository.create_action_log(
                db=db,
                workflow_id=wf.id,
                action_type=WorkflowActionType.APPLICATION_INSPECTION_COMPLETED,
                description=f"Application form inspected (Status: {status_str})."
            )
            db.commit()
            db.refresh(wf)
            return inspect_res.model_dump() if hasattr(inspect_res, "model_dump") else (inspect_res.dict() if hasattr(inspect_res, "dict") else {})
        except Exception as e:
            wf.workflow_status = WorkflowStatus.FAILED.value
            wf.last_error = str(e)
            WorkflowRepository.create_action_log(
                db=db,
                workflow_id=wf.id,
                action_type=WorkflowActionType.WORKFLOW_FAILED,
                description=f"Application inspection failed: {e}",
                status="FAILED"
            )
            db.commit()
            db.refresh(wf)
            raise WorkflowException(
                code=WorkflowErrorCode.APPLICATION_INSPECTION_FAILED,
                message=f"Application inspection failed: {e}",
                workflow_id=wf.id
            )

    @classmethod
    def _handle_checkpoint(
        cls,
        db: Session,
        wf: AutonomousWorkflow,
        reason: PauseReason,
        action_type: UserActionType,
        instructions: str
    ):
        wf.workflow_status = WorkflowStatus.AWAITING_USER_ACTION.value
        wf.user_action_required = True
        wf.paused = True
        wf.pause_reason = reason.value
        wf.paused_at = datetime.now(timezone.utc)
        wf.next_action = instructions

        WorkflowRepository.create_action_log(
            db=db,
            workflow_id=wf.id,
            action_type=WorkflowActionType.USER_ACTION_REQUIRED,
            description=f"Paused at checkpoint: {reason.value} ({action_type.value}). {instructions}"
        )

    @classmethod
    def autofill_approved_fields(
        cls,
        db: Session,
        workflow_id: int,
        approved_field_ids: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        wf = WorkflowRepository.get_workflow(db, workflow_id)

        # Check approval
        if wf.approval_required:
            raise WorkflowException(
                code=WorkflowErrorCode.APPROVAL_REQUIRED,
                message="Autofill requires explicit user approval before execution.",
                workflow_id=wf.id
            )

        wf.workflow_status = WorkflowStatus.AUTOFILLING.value
        wf.current_step = "AUTOFILLING"
        db.commit()

        try:
            meta = json.loads(wf.metadata_json) if wf.metadata_json else {}
            session_token = meta.get("session_id")

            # Ensure browser session exists in browser session manager
            from app.application_automation.browser import default_browser_engine
            session = None
            if session_token:
                try:
                    session = default_browser_engine.session_manager.get_session(session_token)
                except Exception:
                    session = None

            if not session:
                prof = db.query(UserProfile).first()
                inspect_res = default_browser_engine.inspect_application_page(
                    url=wf.source_url or "https://boards.greenhouse.io/figma/jobs/606",
                    profile=prof
                )
                session_token = inspect_res.session_id
                meta["session_id"] = session_token
                wf.metadata_json = json.dumps(meta)
                db.commit()

            fill_req = FillApprovedFieldsRequest(
                session_id=session_token,
                application_url=wf.source_url or "https://boards.greenhouse.io/figma/jobs/606",
                approved_field_ids=approved_field_ids or ["first_name", "last_name", "email", "phone", "linkedin_url"],
                application_id=wf.application_id
            )
            fill_res = ApplicationAutomationService.fill_form(fill_req)

            wf.workflow_status = WorkflowStatus.SUBMISSION_PENDING.value
            wf.current_step = "SUBMISSION_PENDING"
            wf.next_action = "Review completed application in your browser and manually click Submit"
            wf.user_action_required = True

            # Update step
            steps = WorkflowRepository.get_steps(db, wf.id)
            for s in steps:
                if s.step_name == "AUTOFILL_SAFE_FIELDS":
                    WorkflowRepository.update_step(db, s.id, status=WorkflowStepStatus.COMPLETED)

            WorkflowRepository.create_action_log(
                db=db,
                workflow_id=wf.id,
                action_type=WorkflowActionType.AUTOFILL_COMPLETED,
                description="Autofill completed for approved safe fields. Left on manual submission checkpoint."
            )
            db.commit()
            db.refresh(wf)
            return fill_res.model_dump() if hasattr(fill_res, "model_dump") else (fill_res.dict() if hasattr(fill_res, "dict") else {})
        except Exception as e:
            wf.workflow_status = WorkflowStatus.FAILED.value
            wf.last_error = str(e)
            WorkflowRepository.create_action_log(
                db=db,
                workflow_id=wf.id,
                action_type=WorkflowActionType.WORKFLOW_FAILED,
                description=f"Autofill failed: {e}",
                status="FAILED"
            )
            db.commit()
            db.refresh(wf)
            raise WorkflowException(
                code=WorkflowErrorCode.AUTOFILL_FAILED,
                message=f"Autofill failed: {e}",
                workflow_id=wf.id
            )

    @classmethod
    def confirm_manual_submission(
        cls,
        db: Session,
        workflow_id: int,
        submission_notes: Optional[str] = None
    ) -> AutonomousWorkflow:
        """
        Hard Invariant: Final submission is performed manually by the candidate.
        This endpoint records that the candidate completed manual submission.
        """
        wf = WorkflowRepository.get_workflow(db, workflow_id)
        current_status = WorkflowStatus(wf.workflow_status)

        # Idempotency check
        if current_status in (WorkflowStatus.APPLICATION_COMPLETED, WorkflowStatus.CLOSED):
            return wf

        now = datetime.now(timezone.utc)
        wf.workflow_status = WorkflowStatus.APPLICATION_COMPLETED.value
        wf.completed_at = now
        wf.current_step = "APPLICATION_COMPLETED"
        wf.next_action = "Track application status and scheduled follow-ups in Phase 6 pipeline"
        wf.user_action_required = False
        wf.paused = False
        wf.pause_reason = None
        wf.updated_at = now

        # Update step
        steps = WorkflowRepository.get_steps(db, wf.id)
        for s in steps:
            if s.step_name == "MANUAL_SUBMISSION":
                WorkflowRepository.update_step(db, s.id, status=WorkflowStepStatus.COMPLETED)

        # Update Phase 6 TrackedApplication if linked
        if wf.application_id:
            try:
                from app.application_pipeline.schemas import MarkAppliedRequest
                mark_req = MarkAppliedRequest(
                    applied_at=now,
                    note=submission_notes or "Confirmed manual submission via autonomous workflow"
                )
                ApplicationPipelineService.mark_applied(
                    application_id=wf.application_id,
                    request=mark_req,
                    db=db
                )
            except Exception as e:
                logger.warning(f"Could not mark TrackedApplication #{wf.application_id} applied: {e}")

        WorkflowRepository.create_action_log(
            db=db,
            workflow_id=wf.id,
            action_type=WorkflowActionType.APPLICATION_MARKED_MANUALLY_SUBMITTED,
            description=f"Candidate confirmed manual submission on company portal. {submission_notes or ''}"
        )
        db.commit()
        db.refresh(wf)
        return wf

    @classmethod
    def get_next_action(
        cls,
        db: Session,
        workflow_id: int
    ) -> WorkflowNextActionResponse:
        wf = WorkflowRepository.get_workflow(db, workflow_id)
        current_status = WorkflowStatus(wf.workflow_status)

        action_type = UserActionType.NONE
        instructions = wf.next_action or "No pending user action required."

        if current_status in (WorkflowStatus.QUEUED_FOR_REVIEW, WorkflowStatus.AWAITING_APPROVAL) or wf.approval_required:
            action_type = UserActionType.APPROVE_APPLICATION
            instructions = f"Review opportunity for {wf.role} at {wf.company} and approve workflow start."
        elif current_status == WorkflowStatus.AUTOFILL_READY:
            action_type = UserActionType.REVIEW_AUTOFILL
            instructions = "Review mapped profile fields and approve autofill."
        elif current_status == WorkflowStatus.AWAITING_USER_ACTION:
            if wf.pause_reason == PauseReason.AUTHENTICATION_REQUIRED.value:
                action_type = UserActionType.SIGN_IN
                instructions = "Sign in to the company portal in your browser."
            elif wf.pause_reason == PauseReason.ACCOUNT_CREATION_REQUIRED.value:
                action_type = UserActionType.CREATE_ACCOUNT
                instructions = "Create an account on the company portal."
            elif wf.pause_reason == PauseReason.CAPTCHA_DETECTED.value:
                action_type = UserActionType.SOLVE_CAPTCHA
                instructions = "Solve the CAPTCHA in your browser."
            elif wf.pause_reason == PauseReason.EMAIL_VERIFICATION_REQUIRED.value:
                action_type = UserActionType.VERIFY_EMAIL
                instructions = "Complete email verification or enter OTP in your browser."
            else:
                action_type = UserActionType.OTHER
        elif current_status in (WorkflowStatus.SUBMISSION_PENDING, WorkflowStatus.READY_FOR_FINAL_REVIEW):
            action_type = UserActionType.SUBMIT_APPLICATION_MANUALLY
            instructions = "Review completed application in browser, manually click Submit, then call confirm-manual-submission."
        elif current_status in (WorkflowStatus.APPLICATION_COMPLETED, WorkflowStatus.CLOSED):
            action_type = UserActionType.NONE
            instructions = "Application completed. Monitor interview invitations and follow-up reminders."

        return WorkflowNextActionResponse(
            workflow_id=wf.id,
            status=current_status,
            current_step=wf.current_step,
            next_action=wf.next_action or instructions,
            user_action_required=wf.user_action_required or (action_type != UserActionType.NONE and action_type != UserActionType.CONFIRM_APPLICATION_SUBMITTED),
            action_type=action_type,
            instructions=instructions,
            manual_submission_required=True
        )
