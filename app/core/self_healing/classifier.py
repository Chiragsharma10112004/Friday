import re
from typing import Optional, Dict, Any, Tuple
from app.core.self_healing.schemas import FailureCategory, RiskLevel


class FailureClassifier:
    """
    Intelligently analyzes and classifies failures, exceptions, and test breakages
    into actionable diagnostic categories and risk tiers.
    """

    @classmethod
    def classify(
        cls,
        error_message: str,
        stack_trace: Optional[str] = None,
        error_type: Optional[str] = None
    ) -> Tuple[FailureCategory, RiskLevel]:
        text = f"{error_type or ''} {error_message} {stack_trace or ''}".lower()

        # 1. Syntax / Parsing Errors
        if any(kw in text for kw in ("syntaxerror", "indentationerror", "taberror", "invalid syntax")):
            return FailureCategory.SYNTAX_ERROR, RiskLevel.LOW

        # 2. Import / Missing Module
        if any(kw in text for kw in ("modulenotfounderror", "importerror", "cannot import name", "no module named")):
            return FailureCategory.IMPORT_ERROR, RiskLevel.LOW

        # 3. Test Failures
        if any(kw in text for kw in ("assertionerror", "failed (failures=", "failed (errors=", "fail: test_")):
            return FailureCategory.TEST_FAILURE, RiskLevel.MEDIUM

        # 4. Timeout
        if any(kw in text for kw in ("timeoutexpired", "timed out after", "timeout error")):
            return FailureCategory.TIMEOUT, RiskLevel.MEDIUM

        # 5. Configuration
        if any(kw in text for kw in ("configuration_error", "missing environment variable", "database_url invalid", "not null constraint failed")):
            return FailureCategory.CONFIGURATION_ERROR, RiskLevel.HIGH

        # 6. Runtime exceptions
        if any(kw in text for kw in ("attributeerror", "typeerror", "valueerror", "keyerror", "zerodivisionerror", "indexerror")):
            return FailureCategory.RUNTIME_EXCEPTION, RiskLevel.MEDIUM

        return FailureCategory.UNKNOWN, RiskLevel.HIGH
