from typing import List, Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.core.self_healing.schemas import (
    DiagnosticReport,
    RemediationProposal,
    RemediationResult,
    SelfHealingAuditRecord,
)
from app.core.self_healing.service import default_self_healing_service

router = APIRouter(prefix="/self-healing", tags=["Self-Healing & Diagnostic Recovery"])


class DiagnoseRequest(BaseModel):
    error_message: str = Field(..., description="Error message or exception description")
    traceback_text: str = Field(..., description="Traceback or test failure output")
    error_type: Optional[str] = Field(None, description="Exception type (e.g. ValueError, SyntaxError)")


class AutoHealRequest(BaseModel):
    error_message: str
    traceback_text: str
    error_type: Optional[str] = None
    approved: bool = True
    proposed_code_override: Optional[str] = None
    custom_validation_cmd: Optional[str] = None


class ExecuteRemediationRequest(BaseModel):
    approved: bool = True


@router.post(
    "/diagnose",
    response_model=DiagnosticReport,
    summary="Collect and classify failure diagnostics from an exception or traceback"
)
def diagnose_error(req: DiagnoseRequest):
    return default_self_healing_service.diagnose(
        error_message=req.error_message,
        traceback_text=req.traceback_text,
        error_type=req.error_type,
    )


@router.post(
    "/plan",
    response_model=RemediationProposal,
    summary="Generate a structured remediation proposal with diff preview and validation criteria"
)
def plan_remediation(report: DiagnosticReport):
    return default_self_healing_service.plan(report=report)


@router.post(
    "/execute/{proposal_id}",
    response_model=RemediationResult,
    summary="Execute a planned remediation proposal with automatic rollback on failure"
)
def execute_remediation(proposal_id: str, req: ExecuteRemediationRequest):
    try:
        return default_self_healing_service.execute_proposal(
            proposal_id=proposal_id,
            approved=req.approved,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post(
    "/auto-heal",
    response_model=RemediationResult,
    summary="End-to-end self-healing: diagnose, formulate fix, apply edit, and validate"
)
def auto_heal(req: AutoHealRequest):
    return default_self_healing_service.auto_heal(
        error_message=req.error_message,
        traceback_text=req.traceback_text,
        error_type=req.error_type,
        approved=req.approved,
        proposed_code_override=req.proposed_code_override,
        custom_validation_cmd=req.custom_validation_cmd,
    )


@router.get(
    "/history",
    response_model=List[SelfHealingAuditRecord],
    summary="List audit log history of all self-healing operations"
)
def get_healing_history():
    return default_self_healing_service.get_audit_history()
