from typing import Dict, Set, Optional, Any
from datetime import datetime, timezone

from app.application_pipeline.schemas import ApplicationStatus
from app.application_pipeline.errors import PipelineErrorCode, PipelineException


class StatusTransitionEngine:
    """
    Validates and applies lifecycle status transitions for tracked job applications.
    """

    VALID_TRANSITIONS: Dict[ApplicationStatus, Set[ApplicationStatus]] = {
        ApplicationStatus.DISCOVERED: {
            ApplicationStatus.SAVED,
            ApplicationStatus.ASSETS_READY,
            ApplicationStatus.READY_TO_APPLY,
            ApplicationStatus.APPLIED,
            ApplicationStatus.WITHDRAWN,
            ApplicationStatus.CLOSED,
        },
        ApplicationStatus.SAVED: {
            ApplicationStatus.ASSETS_READY,
            ApplicationStatus.READY_TO_APPLY,
            ApplicationStatus.APPLIED,
            ApplicationStatus.WITHDRAWN,
            ApplicationStatus.CLOSED,
        },
        ApplicationStatus.ASSETS_READY: {
            ApplicationStatus.READY_TO_APPLY,
            ApplicationStatus.APPLIED,
            ApplicationStatus.WITHDRAWN,
            ApplicationStatus.CLOSED,
        },
        ApplicationStatus.READY_TO_APPLY: {
            ApplicationStatus.APPLIED,
            ApplicationStatus.WITHDRAWN,
            ApplicationStatus.CLOSED,
        },
        ApplicationStatus.APPLIED: {
            ApplicationStatus.INTERVIEWING,
            ApplicationStatus.OFFER,
            ApplicationStatus.REJECTED,
            ApplicationStatus.WITHDRAWN,
            ApplicationStatus.CLOSED,
        },
        ApplicationStatus.INTERVIEWING: {
            ApplicationStatus.OFFER,
            ApplicationStatus.REJECTED,
            ApplicationStatus.WITHDRAWN,
            ApplicationStatus.CLOSED,
        },
        ApplicationStatus.OFFER: {
            ApplicationStatus.CLOSED,
            ApplicationStatus.WITHDRAWN,
        },
        ApplicationStatus.REJECTED: {
            ApplicationStatus.CLOSED,
        },
        ApplicationStatus.WITHDRAWN: {
            ApplicationStatus.CLOSED,
        },
        ApplicationStatus.CLOSED: set(),  # CLOSED is terminal
    }

    @classmethod
    def validate_transition(
        cls,
        from_status: ApplicationStatus,
        to_status: ApplicationStatus,
        application_id: Optional[int] = None
    ) -> bool:
        """
        Validates if transition from `from_status` to `to_status` is permitted.
        """
        if from_status == to_status:
            return True

        if from_status == ApplicationStatus.CLOSED:
            raise PipelineException(
                code=PipelineErrorCode.INVALID_STATUS_TRANSITION,
                message=f"Application is in CLOSED terminal state and cannot transition to '{to_status.value}'.",
                application_id=application_id
            )

        allowed_targets = cls.VALID_TRANSITIONS.get(from_status, set())
        if to_status not in allowed_targets:
            raise PipelineException(
                code=PipelineErrorCode.INVALID_STATUS_TRANSITION,
                message=f"Invalid status transition from '{from_status.value}' to '{to_status.value}'. Allowed transitions: {[s.value for s in allowed_targets]}",
                application_id=application_id
            )

        return True

    @classmethod
    def apply_transition_timestamps(
        cls,
        app_record: Any,
        to_status: ApplicationStatus,
        now: Optional[datetime] = None
    ):
        """
        Updates relevant lifecycle timestamp fields on the model instance.
        """
        now = now or datetime.now(timezone.utc)
        app_record.last_status_update = now

        if to_status == ApplicationStatus.SAVED and not app_record.date_saved:
            app_record.date_saved = now
        elif to_status == ApplicationStatus.ASSETS_READY and not app_record.date_assets_generated:
            app_record.date_assets_generated = now
        elif to_status == ApplicationStatus.APPLIED and not app_record.date_applied:
            app_record.date_applied = now
        elif to_status == ApplicationStatus.OFFER and not app_record.offer_date:
            app_record.offer_date = now
        elif to_status == ApplicationStatus.REJECTED and not app_record.rejection_date:
            app_record.rejection_date = now
        elif to_status == ApplicationStatus.WITHDRAWN and not app_record.withdrawal_date:
            app_record.withdrawal_date = now

