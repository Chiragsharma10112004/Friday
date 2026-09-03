import json
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import desc, func

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
    WorkflowQueueItem,
    WorkflowQueueResponse,
    WorkflowDashboardResponse,
)
from app.autonomous_workflow.errors import WorkflowErrorCode, WorkflowException


class WorkflowRepository:
    """
    Persistence layer for Autonomous Workflows, steps, approvals, audit logs, and retries.
    """

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
        match_score: Optional[int] = None,
        recommendation_score: Optional[int] = None,
        initial_status: WorkflowStatus = WorkflowStatus.CREATED,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> AutonomousWorkflow:
        wf = AutonomousWorkflow(
            profile_id=profile_id,
            application_id=application_id,
            opportunity_id=opportunity_id,
            company=company,
            role=role,
            source_url=source_url,
            source_platform=source_platform,
            workflow_status=initial_status.value,
            workflow_priority=priority.value,
            match_score=match_score,
            recommendation_score=recommendation_score,
            current_step=initial_status.value,
            next_action="Initialize application execution plan",
            metadata_json=json.dumps(metadata) if metadata else None,
        )
        db.add(wf)
        db.commit()
        db.refresh(wf)

        # Log creation action
        cls.create_action_log(
            db=db,
            workflow_id=wf.id,
            action_type=WorkflowActionType.WORKFLOW_CREATED,
            description=f"Workflow initialized for {role} at {company} (Priority: {priority.value}).",
        )
        return wf

    @classmethod
    def get_workflow(cls, db: Session, workflow_id: int) -> AutonomousWorkflow:
        wf = db.query(AutonomousWorkflow).filter(AutonomousWorkflow.id == workflow_id).first()
        if not wf:
            raise WorkflowException(
                code=WorkflowErrorCode.WORKFLOW_NOT_FOUND,
                message=f"Workflow with ID {workflow_id} not found.",
                workflow_id=workflow_id
            )
        return wf

    @classmethod
    def get_workflow_by_opportunity(cls, db: Session, opportunity_id: int) -> Optional[AutonomousWorkflow]:
        return db.query(AutonomousWorkflow).filter(
            AutonomousWorkflow.opportunity_id == opportunity_id
        ).first()

    @classmethod
    def get_workflow_by_application(cls, db: Session, application_id: int) -> Optional[AutonomousWorkflow]:
        return db.query(AutonomousWorkflow).filter(
            AutonomousWorkflow.application_id == application_id
        ).first()

    @classmethod
    def check_duplicate_workflow(
        cls,
        db: Session,
        company: str,
        role: str,
        opportunity_id: Optional[int] = None,
        application_id: Optional[int] = None
    ) -> Optional[AutonomousWorkflow]:
        query = db.query(AutonomousWorkflow).filter(
            AutonomousWorkflow.workflow_status.notin_([
                WorkflowStatus.CANCELLED.value,
                WorkflowStatus.CLOSED.value
            ])
        )
        if opportunity_id:
            match = query.filter(AutonomousWorkflow.opportunity_id == opportunity_id).first()
            if match:
                return match
        if application_id:
            match = query.filter(AutonomousWorkflow.application_id == application_id).first()
            if match:
                return match

        return query.filter(
            func.lower(AutonomousWorkflow.company) == company.lower().strip(),
            func.lower(AutonomousWorkflow.role) == role.lower().strip()
        ).first()

    @classmethod
    def list_workflows(
        cls,
        db: Session,
        priority: Optional[WorkflowPriority] = None,
        status: Optional[WorkflowStatus] = None,
        company: Optional[str] = None,
        min_match_score: Optional[int] = None,
        user_action_required: Optional[bool] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> Tuple[List[AutonomousWorkflow], int]:
        query = db.query(AutonomousWorkflow)

        if priority:
            query = query.filter(AutonomousWorkflow.workflow_priority == priority.value)
        if status:
            query = query.filter(AutonomousWorkflow.workflow_status == status.value)
        if company:
            query = query.filter(AutonomousWorkflow.company.ilike(f"%{company}%"))
        if min_match_score is not None:
            query = query.filter(AutonomousWorkflow.match_score >= min_match_score)
        if user_action_required is not None:
            query = query.filter(AutonomousWorkflow.user_action_required == user_action_required)

        total = query.count()
        items = query.order_by(desc(AutonomousWorkflow.updated_at)).offset(skip).limit(limit).all()
        return items, total

    @classmethod
    def create_step(
        cls,
        db: Session,
        workflow_id: int,
        step_name: str,
        step_order: int,
        status: WorkflowStepStatus = WorkflowStepStatus.PENDING,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> WorkflowStep:
        step = WorkflowStep(
            workflow_id=workflow_id,
            step_name=step_name,
            step_order=step_order,
            status=status.value,
            metadata_json=json.dumps(metadata) if metadata else None,
        )
        db.add(step)
        db.commit()
        db.refresh(step)
        return step

    @classmethod
    def update_step(
        cls,
        db: Session,
        step_id: int,
        status: Optional[WorkflowStepStatus] = None,
        error_message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> WorkflowStep:
        step = db.query(WorkflowStep).filter(WorkflowStep.id == step_id).first()
        if not step:
            raise WorkflowException(
                code=WorkflowErrorCode.WORKFLOW_NOT_FOUND,
                message=f"Step with ID {step_id} not found."
            )

        now = datetime.now(timezone.utc)
        if status:
            step.status = status.value
            if status == WorkflowStepStatus.RUNNING and not step.started_at:
                step.started_at = now
            elif status in (WorkflowStepStatus.COMPLETED, WorkflowStepStatus.FAILED, WorkflowStepStatus.SKIPPED):
                step.completed_at = now

        if error_message:
            step.error_message = error_message
        if metadata:
            existing = json.loads(step.metadata_json) if step.metadata_json else {}
            existing.update(metadata)
            step.metadata_json = json.dumps(existing)

        db.commit()
        db.refresh(step)
        return step

    @classmethod
    def get_steps(cls, db: Session, workflow_id: int) -> List[WorkflowStep]:
        return db.query(WorkflowStep).filter(
            WorkflowStep.workflow_id == workflow_id
        ).order_by(WorkflowStep.step_order).all()

    @classmethod
    def create_approval(
        cls,
        db: Session,
        workflow_id: int,
        approval_type: ApprovalType,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> WorkflowApproval:
        appr = WorkflowApproval(
            workflow_id=workflow_id,
            approval_type=approval_type.value,
            status=ApprovalStatus.PENDING.value,
            metadata_json=json.dumps(metadata) if metadata else None,
        )
        db.add(appr)
        db.commit()
        db.refresh(appr)
        return appr

    @classmethod
    def list_approvals(
        cls,
        db: Session,
        workflow_id: Optional[int] = None,
        status: Optional[ApprovalStatus] = None,
    ) -> List[WorkflowApproval]:
        query = db.query(WorkflowApproval)
        if workflow_id:
            query = query.filter(WorkflowApproval.workflow_id == workflow_id)
        if status:
            query = query.filter(WorkflowApproval.status == status.value)
        return query.order_by(desc(WorkflowApproval.requested_at)).all()

    @classmethod
    def create_action_log(
        cls,
        db: Session,
        workflow_id: int,
        action_type: WorkflowActionType,
        description: str,
        status: str = "SUCCESS",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> WorkflowActionLog:
        log = WorkflowActionLog(
            workflow_id=workflow_id,
            action_type=action_type.value,
            description=description,
            status=status,
            metadata_json=json.dumps(metadata) if metadata else None,
        )
        db.add(log)
        db.commit()
        db.refresh(log)
        return log

    @classmethod
    def get_action_logs(cls, db: Session, workflow_id: int) -> List[WorkflowActionLog]:
        return db.query(WorkflowActionLog).filter(
            WorkflowActionLog.workflow_id == workflow_id
        ).order_by(desc(WorkflowActionLog.timestamp)).all()

    @classmethod
    def get_queue_summary(cls, db: Session) -> WorkflowQueueResponse:
        all_active = db.query(AutonomousWorkflow).all()

        urgent_items: List[WorkflowQueueItem] = []
        high_prio_items: List[WorkflowQueueItem] = []
        ready_for_approval_items: List[WorkflowQueueItem] = []
        ready_for_assets_items: List[WorkflowQueueItem] = []
        ready_for_autofill_items: List[WorkflowQueueItem] = []
        awaiting_user_action_items: List[WorkflowQueueItem] = []
        awaiting_manual_review_items: List[WorkflowQueueItem] = []
        ready_for_submission_items: List[WorkflowQueueItem] = []
        paused_items: List[WorkflowQueueItem] = []
        failed_items: List[WorkflowQueueItem] = []
        completed_items: List[WorkflowQueueItem] = []

        for wf in all_active:
            try:
                w_status = WorkflowStatus(wf.workflow_status)
            except ValueError:
                w_status = WorkflowStatus.CREATED

            try:
                w_prio = WorkflowPriority(wf.workflow_priority)
            except ValueError:
                w_prio = WorkflowPriority.MEDIUM

            item = WorkflowQueueItem(
                workflow_id=wf.id,
                application_id=wf.application_id,
                opportunity_id=wf.opportunity_id,
                company=wf.company,
                role=wf.role,
                match_score=wf.match_score,
                priority=w_prio,
                workflow_status=w_status,
                current_step=wf.current_step,
                next_action=wf.next_action,
                pause_reason=wf.pause_reason,
                user_action_required=wf.user_action_required,
                created_at=wf.created_at,
                updated_at=wf.updated_at,
            )

            # Categorize
            if w_prio == WorkflowPriority.URGENT and w_status not in (WorkflowStatus.APPLICATION_COMPLETED, WorkflowStatus.CLOSED, WorkflowStatus.CANCELLED):
                urgent_items.append(item)
            elif w_prio == WorkflowPriority.HIGH and w_status not in (WorkflowStatus.APPLICATION_COMPLETED, WorkflowStatus.CLOSED, WorkflowStatus.CANCELLED):
                high_prio_items.append(item)

            if w_status in (WorkflowStatus.QUEUED_FOR_REVIEW, WorkflowStatus.AWAITING_APPROVAL) or wf.approval_required:
                ready_for_approval_items.append(item)
            elif w_status in (WorkflowStatus.APPROVED, WorkflowStatus.PLANNING):
                ready_for_assets_items.append(item)
            elif w_status == WorkflowStatus.AUTOFILL_READY:
                ready_for_autofill_items.append(item)
            elif w_status == WorkflowStatus.AWAITING_USER_ACTION or wf.user_action_required:
                awaiting_user_action_items.append(item)
            elif w_status == WorkflowStatus.AWAITING_MANUAL_REVIEW:
                awaiting_manual_review_items.append(item)
            elif w_status in (WorkflowStatus.READY_FOR_FINAL_REVIEW, WorkflowStatus.SUBMISSION_PENDING):
                ready_for_submission_items.append(item)
            elif w_status == WorkflowStatus.PAUSED or wf.paused:
                paused_items.append(item)
            elif w_status == WorkflowStatus.FAILED:
                failed_items.append(item)
            elif w_status in (WorkflowStatus.APPLICATION_COMPLETED, WorkflowStatus.CLOSED):
                completed_items.append(item)

        return WorkflowQueueResponse(
            total=len(all_active),
            urgent=urgent_items,
            high_priority=high_prio_items,
            ready_for_approval=ready_for_approval_items,
            ready_for_assets=ready_for_assets_items,
            ready_for_autofill=ready_for_autofill_items,
            awaiting_user_action=awaiting_user_action_items,
            awaiting_manual_review=awaiting_manual_review_items,
            ready_for_submission=ready_for_submission_items,
            paused=paused_items,
            failed=failed_items,
            completed=completed_items,
        )

    @classmethod
    def get_dashboard_summary(cls, db: Session) -> WorkflowDashboardResponse:
        queue = cls.get_queue_summary(db)
        all_wfs = db.query(AutonomousWorkflow).all()

        active_count = sum(1 for w in all_wfs if w.workflow_status not in (WorkflowStatus.APPLICATION_COMPLETED.value, WorkflowStatus.CLOSED.value, WorkflowStatus.CANCELLED.value))

        scores = [w.match_score for w in all_wfs if w.match_score is not None]
        avg_score = round(sum(scores) / len(scores), 1) if scores else None

        comp_counts: Dict[str, int] = {}
        for w in all_wfs:
            comp_counts[w.company] = comp_counts.get(w.company, 0) + 1

        recent_logs = db.query(WorkflowActionLog).order_by(desc(WorkflowActionLog.timestamp)).limit(10).all()
        recent_log_schemas = [l.to_schema() for l in recent_logs]

        status_dist: Dict[str, int] = {}
        for w in all_wfs:
            status_dist[w.workflow_status] = status_dist.get(w.workflow_status, 0) + 1

        return WorkflowDashboardResponse(
            total_active_workflows=active_count,
            awaiting_approval=len(queue.ready_for_approval),
            awaiting_user_action=len(queue.awaiting_user_action),
            ready_for_submission=len(queue.ready_for_submission),
            paused=len(queue.paused),
            failed=len(queue.failed),
            completed=len(queue.completed),
            high_priority_count=len(queue.high_priority),
            urgent_count=len(queue.urgent),
            average_match_score=avg_score,
            top_companies=comp_counts,
            recent_activity=recent_log_schemas,
            upcoming_follow_ups=0,
            referral_pending_count=0,
            application_status_distribution=status_dist,
        )
