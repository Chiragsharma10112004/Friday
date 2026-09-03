from datetime import datetime, timezone
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session

from app.autonomous_workflow.models import AutonomousWorkflow, WorkflowActionLog
from app.autonomous_workflow.schemas import WorkflowActionType
from app.application_pipeline.models import TrackedApplication
from app.application_pipeline.schemas import ReferralStatus


class WorkflowReferralManager:
    """
    Manages referral recommendations, tracking, and outreach preparation within autonomous workflows.
    Ensures zero automated external communication while providing structured assistance.
    """

    @classmethod
    def should_recommend_referral(
        cls,
        workflow: AutonomousWorkflow,
        app: Optional[TrackedApplication] = None
    ) -> bool:
        """
        Determines whether seeking an employee referral should be proactively recommended.

        Args:
            workflow: The active autonomous workflow entity.
            app: Optional associated TrackedApplication entity.

        Returns:
            True if candidate match score >= 70% and no referral is currently active or pending.
        """
        if app and app.referral_status in (ReferralStatus.REFERRED.value, ReferralStatus.REFERRAL_PENDING.value):
            return False
        return (workflow.match_score or 0) >= 70

    @classmethod
    def update_referral_state(
        cls,
        db: Session,
        workflow: AutonomousWorkflow,
        referral_contact_name: Optional[str] = None,
        referral_contact_identifier: Optional[str] = None,
        referral_status: Optional[str] = None,
        referral_notes: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Updates referral tracking details on the associated TrackedApplication and logs an audit trail event.

        Args:
            db: SQLAlchemy database session.
            workflow: AutonomousWorkflow instance being updated.
            referral_contact_name: Name of the employee/contact providing the referral.
            referral_contact_identifier: Email, LinkedIn handle, or employee ID of the referrer.
            referral_status: Target ReferralStatus enum value (e.g. REQUESTED, REFERRED).
            referral_notes: User notes or guidance regarding the referral outreach.

        Returns:
            Dict containing the updated referral tracking state.
        """
        app: Optional[TrackedApplication] = None
        if workflow.application_id:
            app = db.query(TrackedApplication).filter(TrackedApplication.id == workflow.application_id).first()

        now = datetime.now(timezone.utc)
        status_val = referral_status or (ReferralStatus.REQUESTED.value if referral_contact_name else ReferralStatus.NOT_REQUESTED.value)

        if app:
            if referral_contact_name:
                app.referral_contact_name = referral_contact_name
            if referral_contact_identifier:
                app.referral_contact_identifier = referral_contact_identifier
            if referral_notes:
                app.referral_notes = referral_notes
            app.referral_status = status_val
            if status_val == ReferralStatus.REQUESTED.value and not app.referral_requested_date:
                app.referral_requested_date = now
            elif status_val == ReferralStatus.REFERRED.value and not app.referral_referred_date:
                app.referral_referred_date = now

        # Add audit log
        log_entry = WorkflowActionLog(
            workflow_id=workflow.id,
            action_type=WorkflowActionType.REFERRAL_REQUESTED.value if status_val == ReferralStatus.REQUESTED.value else WorkflowActionType.REFERRAL_RECOMMENDED.value,
            description=f"Referral state updated to '{status_val}' for {workflow.company}.",
            status="SUCCESS",
            timestamp=now
        )
        db.add(log_entry)
        db.commit()

        return {
            "workflow_id": workflow.id,
            "referral_status": status_val,
            "referral_contact_name": referral_contact_name or (app.referral_contact_name if app else None),
            "referral_contact_identifier": referral_contact_identifier or (app.referral_contact_identifier if app else None),
            "referral_notes": referral_notes or (app.referral_notes if app else None),
        }
