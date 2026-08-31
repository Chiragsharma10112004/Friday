from typing import Set, Dict, List, Optional, Union
from app.autonomous_workflow.schemas import WorkflowStatus
from app.autonomous_workflow.errors import WorkflowErrorCode, WorkflowException


class WorkflowStateMachine:
    """
    Strict state transition validator and lifecycle manager for autonomous workflows.
    """

    _TRANSITIONS: Dict[WorkflowStatus, Set[WorkflowStatus]] = {
        WorkflowStatus.CREATED: {
            WorkflowStatus.DISCOVERED,
            WorkflowStatus.ANALYZING,
            WorkflowStatus.QUEUED_FOR_REVIEW,
            WorkflowStatus.AWAITING_APPROVAL,
            WorkflowStatus.APPROVED,
            WorkflowStatus.PLANNING,
            WorkflowStatus.PAUSED,
            WorkflowStatus.FAILED,
            WorkflowStatus.CANCELLED,
        },
        WorkflowStatus.DISCOVERED: {
            WorkflowStatus.ANALYZING,
            WorkflowStatus.QUEUED_FOR_REVIEW,
            WorkflowStatus.AWAITING_APPROVAL,
            WorkflowStatus.PAUSED,
            WorkflowStatus.FAILED,
            WorkflowStatus.CANCELLED,
        },
        WorkflowStatus.ANALYZING: {
            WorkflowStatus.ANALYZED,
            WorkflowStatus.SCORED,
            WorkflowStatus.QUEUED_FOR_REVIEW,
            WorkflowStatus.PAUSED,
            WorkflowStatus.FAILED,
            WorkflowStatus.CANCELLED,
        },
        WorkflowStatus.ANALYZED: {
            WorkflowStatus.SCORED,
            WorkflowStatus.QUEUED_FOR_REVIEW,
            WorkflowStatus.AWAITING_APPROVAL,
            WorkflowStatus.PLANNING,
            WorkflowStatus.PAUSED,
            WorkflowStatus.FAILED,
            WorkflowStatus.CANCELLED,
        },
        WorkflowStatus.SCORED: {
            WorkflowStatus.QUEUED_FOR_REVIEW,
            WorkflowStatus.AWAITING_APPROVAL,
            WorkflowStatus.APPROVED,
            WorkflowStatus.PLANNING,
            WorkflowStatus.PAUSED,
            WorkflowStatus.FAILED,
            WorkflowStatus.CANCELLED,
        },
        WorkflowStatus.QUEUED_FOR_REVIEW: {
            WorkflowStatus.AWAITING_APPROVAL,
            WorkflowStatus.APPROVED,
            WorkflowStatus.PLANNING,
            WorkflowStatus.PAUSED,
            WorkflowStatus.FAILED,
            WorkflowStatus.CANCELLED,
        },
        WorkflowStatus.AWAITING_APPROVAL: {
            WorkflowStatus.APPROVED,
            WorkflowStatus.AWAITING_USER_ACTION,
            WorkflowStatus.PLANNING,
            WorkflowStatus.PAUSED,
            WorkflowStatus.FAILED,
            WorkflowStatus.CANCELLED,
        },
        WorkflowStatus.APPROVED: {
            WorkflowStatus.PLANNING,
            WorkflowStatus.ASSETS_GENERATING,
            WorkflowStatus.APPLICATION_INSPECTING,
            WorkflowStatus.PAUSED,
            WorkflowStatus.FAILED,
            WorkflowStatus.CANCELLED,
        },
        WorkflowStatus.PLANNING: {
            WorkflowStatus.ASSETS_GENERATING,
            WorkflowStatus.ASSETS_READY,
            WorkflowStatus.APPLICATION_INSPECTING,
            WorkflowStatus.AWAITING_APPROVAL,
            WorkflowStatus.PAUSED,
            WorkflowStatus.FAILED,
            WorkflowStatus.CANCELLED,
        },
        WorkflowStatus.ASSETS_GENERATING: {
            WorkflowStatus.ASSETS_READY,
            WorkflowStatus.APPLICATION_INSPECTING,
            WorkflowStatus.PAUSED,
            WorkflowStatus.FAILED,
            WorkflowStatus.CANCELLED,
        },
        WorkflowStatus.ASSETS_READY: {
            WorkflowStatus.APPLICATION_INSPECTING,
            WorkflowStatus.APPLICATION_INSPECTED,
            WorkflowStatus.AUTOFILL_READY,
            WorkflowStatus.AWAITING_APPROVAL,
            WorkflowStatus.PAUSED,
            WorkflowStatus.FAILED,
            WorkflowStatus.CANCELLED,
        },
        WorkflowStatus.APPLICATION_INSPECTING: {
            WorkflowStatus.APPLICATION_INSPECTED,
            WorkflowStatus.AUTOFILL_READY,
            WorkflowStatus.AWAITING_USER_ACTION,
            WorkflowStatus.PAUSED,
            WorkflowStatus.FAILED,
            WorkflowStatus.CANCELLED,
        },
        WorkflowStatus.APPLICATION_INSPECTED: {
            WorkflowStatus.AUTOFILL_READY,
            WorkflowStatus.AWAITING_APPROVAL,
            WorkflowStatus.AWAITING_USER_ACTION,
            WorkflowStatus.PAUSED,
            WorkflowStatus.FAILED,
            WorkflowStatus.CANCELLED,
        },
        WorkflowStatus.AUTOFILL_READY: {
            WorkflowStatus.AWAITING_APPROVAL,
            WorkflowStatus.AUTOFILLING,
            WorkflowStatus.AWAITING_USER_ACTION,
            WorkflowStatus.PAUSED,
            WorkflowStatus.FAILED,
            WorkflowStatus.CANCELLED,
        },
        WorkflowStatus.AUTOFILLING: {
            WorkflowStatus.AWAITING_USER_ACTION,
            WorkflowStatus.AWAITING_MANUAL_REVIEW,
            WorkflowStatus.READY_FOR_FINAL_REVIEW,
            WorkflowStatus.SUBMISSION_PENDING,
            WorkflowStatus.PAUSED,
            WorkflowStatus.FAILED,
            WorkflowStatus.CANCELLED,
        },
        WorkflowStatus.AWAITING_USER_ACTION: {
            WorkflowStatus.AUTOFILLING,
            WorkflowStatus.APPLICATION_INSPECTING,
            WorkflowStatus.AWAITING_MANUAL_REVIEW,
            WorkflowStatus.READY_FOR_FINAL_REVIEW,
            WorkflowStatus.SUBMISSION_PENDING,
            WorkflowStatus.PAUSED,
            WorkflowStatus.FAILED,
            WorkflowStatus.CANCELLED,
        },
        WorkflowStatus.AWAITING_MANUAL_REVIEW: {
            WorkflowStatus.READY_FOR_FINAL_REVIEW,
            WorkflowStatus.SUBMISSION_PENDING,
            WorkflowStatus.APPLICATION_COMPLETED,
            WorkflowStatus.PAUSED,
            WorkflowStatus.FAILED,
            WorkflowStatus.CANCELLED,
        },
        WorkflowStatus.READY_FOR_FINAL_REVIEW: {
            WorkflowStatus.SUBMISSION_PENDING,
            WorkflowStatus.APPLICATION_COMPLETED,
            WorkflowStatus.PAUSED,
            WorkflowStatus.FAILED,
            WorkflowStatus.CANCELLED,
        },
        WorkflowStatus.SUBMISSION_PENDING: {
            WorkflowStatus.APPLICATION_COMPLETED,
            WorkflowStatus.PAUSED,
            WorkflowStatus.FAILED,
            WorkflowStatus.CANCELLED,
        },
        WorkflowStatus.APPLICATION_COMPLETED: {
            WorkflowStatus.CLOSED,
        },
        WorkflowStatus.PAUSED: {
            WorkflowStatus.CREATED,
            WorkflowStatus.DISCOVERED,
            WorkflowStatus.ANALYZING,
            WorkflowStatus.ANALYZED,
            WorkflowStatus.SCORED,
            WorkflowStatus.QUEUED_FOR_REVIEW,
            WorkflowStatus.AWAITING_APPROVAL,
            WorkflowStatus.APPROVED,
            WorkflowStatus.PLANNING,
            WorkflowStatus.ASSETS_GENERATING,
            WorkflowStatus.ASSETS_READY,
            WorkflowStatus.APPLICATION_INSPECTING,
            WorkflowStatus.APPLICATION_INSPECTED,
            WorkflowStatus.AUTOFILL_READY,
            WorkflowStatus.AUTOFILLING,
            WorkflowStatus.AWAITING_USER_ACTION,
            WorkflowStatus.AWAITING_MANUAL_REVIEW,
            WorkflowStatus.READY_FOR_FINAL_REVIEW,
            WorkflowStatus.SUBMISSION_PENDING,
            WorkflowStatus.CANCELLED,
            WorkflowStatus.CLOSED,
        },
        WorkflowStatus.FAILED: {
            WorkflowStatus.CREATED,
            WorkflowStatus.ANALYZING,
            WorkflowStatus.PLANNING,
            WorkflowStatus.ASSETS_GENERATING,
            WorkflowStatus.APPLICATION_INSPECTING,
            WorkflowStatus.AUTOFILLING,
            WorkflowStatus.CANCELLED,
            WorkflowStatus.CLOSED,
        },
        WorkflowStatus.CANCELLED: set(),
        WorkflowStatus.CLOSED: set(),
    }

    TERMINAL_STATES = {WorkflowStatus.CANCELLED, WorkflowStatus.CLOSED}

    @classmethod
    def _coerce_status(cls, status: Union[WorkflowStatus, str, None]) -> Optional[WorkflowStatus]:
        """Defensively coerces a WorkflowStatus enum or string to a validated WorkflowStatus."""
        if isinstance(status, WorkflowStatus):
            return status
        if isinstance(status, str):
            try:
                return WorkflowStatus(status)
            except ValueError:
                return None
        return None

    @classmethod
    def can_transition(cls, from_status: Union[WorkflowStatus, str], to_status: Union[WorkflowStatus, str]) -> bool:
        """Determines whether a transition between two workflow statuses is permitted."""
        f_enum = cls._coerce_status(from_status)
        t_enum = cls._coerce_status(to_status)
        if f_enum is None or t_enum is None:
            return False
        if f_enum == t_enum:
            return True
        allowed = cls._TRANSITIONS.get(f_enum, set())
        return t_enum in allowed

    @classmethod
    def validate_transition(
        cls,
        from_status: Union[WorkflowStatus, str],
        to_status: Union[WorkflowStatus, str],
        workflow_id: int = 0
    ) -> None:
        """
        Validates transition legality between statuses, raising a WorkflowException on disallowed transitions.
        """
        f_enum = cls._coerce_status(from_status)
        t_enum = cls._coerce_status(to_status)
        from_str = f_enum.value if f_enum else str(from_status)
        to_str = t_enum.value if t_enum else str(to_status)

        if f_enum is None or t_enum is None or not cls.can_transition(f_enum, t_enum):
            raise WorkflowException(
                code=WorkflowErrorCode.INVALID_WORKFLOW_TRANSITION,
                message=f"Cannot transition workflow from '{from_str}' to '{to_str}'.",
                workflow_id=workflow_id,
                details={"from_status": from_str, "to_status": to_str}
            )

    @classmethod
    def get_valid_next_states(cls, current_status: Union[WorkflowStatus, str]) -> List[WorkflowStatus]:
        """Returns the list of valid subsequent workflow statuses from the current state."""
        c_enum = cls._coerce_status(current_status)
        if c_enum is None:
            return []
        return list(cls._TRANSITIONS.get(c_enum, set()))
