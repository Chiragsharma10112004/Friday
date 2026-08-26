from typing import Set, Dict, List
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
    def can_transition(cls, from_status: WorkflowStatus, to_status: WorkflowStatus) -> bool:
        if from_status == to_status:
            return True
        allowed = cls._TRANSITIONS.get(from_status, set())
        return to_status in allowed

    @classmethod
    def validate_transition(cls, from_status: WorkflowStatus, to_status: WorkflowStatus, workflow_id: int = 0):
        if not cls.can_transition(from_status, to_status):
            raise WorkflowException(
                code=WorkflowErrorCode.INVALID_WORKFLOW_TRANSITION,
                message=f"Cannot transition workflow from '{from_status.value}' to '{to_status.value}'.",
                workflow_id=workflow_id,
                details={"from_status": from_status.value, "to_status": to_status.value}
            )

    @classmethod
    def get_valid_next_states(cls, current_status: WorkflowStatus) -> List[WorkflowStatus]:
        return list(cls._TRANSITIONS.get(current_status, set()))
