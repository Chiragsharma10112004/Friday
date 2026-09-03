from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class FailureCategory(str, Enum):
    SYNTAX_ERROR = "SYNTAX_ERROR"
    IMPORT_ERROR = "IMPORT_ERROR"
    TEST_FAILURE = "TEST_FAILURE"
    RUNTIME_EXCEPTION = "RUNTIME_EXCEPTION"
    CONFIGURATION_ERROR = "CONFIGURATION_ERROR"
    DEPENDENCY_MISSING = "DEPENDENCY_MISSING"
    TIMEOUT = "TIMEOUT"
    UNKNOWN = "UNKNOWN"


class RemediationStrategy(str, Enum):
    AST_FUNCTION_REPLACE = "AST_FUNCTION_REPLACE"
    IMPORT_INSERTION = "IMPORT_INSERTION"
    SYNTAX_REPAIR = "SYNTAX_REPAIR"
    CONFIG_CORRECTION = "CONFIG_CORRECTION"
    DEPENDENCY_INSTALL = "DEPENDENCY_INSTALL"
    MANUAL_ESCALATION = "MANUAL_ESCALATION"


class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class RecoveryStatus(str, Enum):
    PENDING_APPROVAL = "PENDING_APPROVAL"
    IN_PROGRESS = "IN_PROGRESS"
    RECOVERED = "RECOVERED"
    VALIDATION_FAILED = "VALIDATION_FAILED"
    ROLLED_BACK = "ROLLED_BACK"
    ESCALATED = "ESCALATED"


class DiagnosticReport(BaseModel):
    category: FailureCategory
    error_type: str
    error_message: str
    target_file: Optional[str] = None
    target_line: Optional[int] = None
    target_symbol: Optional[str] = None
    stack_trace_snippet: Optional[str] = None
    context_code: Optional[str] = None
    failing_tests: List[str] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class RemediationProposal(BaseModel):
    proposal_id: str
    category: FailureCategory
    strategy: RemediationStrategy
    risk_level: RiskLevel
    description: str
    target_file: str
    target_symbol: Optional[str] = None
    proposed_code: Optional[str] = None
    diff_preview: Optional[str] = None
    requires_approval: bool = True
    validation_command: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class RemediationResult(BaseModel):
    proposal_id: str
    status: RecoveryStatus
    strategy_applied: RemediationStrategy
    target_file: str
    diff_applied: Optional[str] = None
    validation_passed: bool = False
    validation_output: Optional[str] = None
    attempts: int = 1
    error: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class SelfHealingAuditRecord(BaseModel):
    id: str
    timestamp: datetime
    category: FailureCategory
    target_file: str
    strategy: RemediationStrategy
    status: RecoveryStatus
    validation_passed: bool
    summary: str

