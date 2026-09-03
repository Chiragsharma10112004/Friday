import uuid
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any

from app.core.self_healing.schemas import (
    DiagnosticReport,
    RemediationProposal,
    RemediationResult,
    SelfHealingAuditRecord,
    RecoveryStatus,
)
from app.core.self_healing.diagnostics import DiagnosticCollector
from app.core.self_healing.planner import RemediationPlanner
from app.core.self_healing.executor import RemediationExecutor


class SelfHealingService:
    """
    Central self-healing service coordinating diagnostic ingestion, remediation planning,
    safe bounded execution, automated rollbacks, and audit logging.
    """

    def __init__(self):
        self._audit_history: List[SelfHealingAuditRecord] = []
        self._pending_proposals: Dict[str, RemediationProposal] = {}

    def diagnose(
        self,
        error_message: str,
        traceback_text: str,
        error_type: Optional[str] = None
    ) -> DiagnosticReport:
        return DiagnosticCollector.collect_from_traceback(
            error_message=error_message,
            traceback_text=traceback_text,
            error_type=error_type,
        )

    def plan(
        self,
        report: DiagnosticReport,
        proposed_code_override: Optional[str] = None,
        custom_validation_cmd: Optional[str] = None,
    ) -> RemediationProposal:
        proposal = RemediationPlanner.plan_remediation(
            report=report,
            proposed_code_override=proposed_code_override,
            custom_validation_cmd=custom_validation_cmd,
        )
        self._pending_proposals[proposal.proposal_id] = proposal
        return proposal

    def execute_proposal(
        self,
        proposal_id: str,
        approved: bool = True
    ) -> RemediationResult:
        proposal = self._pending_proposals.get(proposal_id)
        if not proposal:
            raise ValueError(f"Remediation proposal '{proposal_id}' not found.")

        result = RemediationExecutor.execute(proposal=proposal, approved=approved)

        # Log audit record
        audit = SelfHealingAuditRecord(
            id=str(uuid.uuid4())[:8],
            timestamp=datetime.now(timezone.utc),
            category=proposal.category,
            target_file=proposal.target_file,
            strategy=proposal.strategy,
            status=result.status,
            validation_passed=result.validation_passed,
            summary=f"Remediation {proposal_id} {result.status.value}: {proposal.description}",
        )
        self._audit_history.append(audit)

        return result

    def auto_heal(
        self,
        error_message: str,
        traceback_text: str,
        error_type: Optional[str] = None,
        approved: bool = True,
        proposed_code_override: Optional[str] = None,
        custom_validation_cmd: Optional[str] = None,
    ) -> RemediationResult:
        report = self.diagnose(error_message, traceback_text, error_type)
        proposal = self.plan(report, proposed_code_override, custom_validation_cmd)
        return self.execute_proposal(proposal.proposal_id, approved=approved)

    def get_audit_history(self) -> List[SelfHealingAuditRecord]:
        return list(reversed(self._audit_history))


default_self_healing_service = SelfHealingService()
