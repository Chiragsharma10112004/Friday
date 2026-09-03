import logging
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session

from app.application_feedback.models import ApplicationFieldIssue
from app.application_feedback.schemas import FieldIssueType, FieldIssueResponse
from app.application_feedback.repository import FeedbackRepository

logger = logging.getLogger("friday.application_feedback.field_issues")


class FieldIssueTracker:
    """
    Diagnoses and tracks form-field inspection, validation, and autofill failures
    across ATS platforms with strict safety guarantees (zero credential or sensitive data retention).
    """

    SENSITIVE_FIELD_PATTERNS = {"password", "passwd", "otp", "token", "ssn", "secret", "card", "cvv", "pin"}

    @classmethod
    def sanitize_field_name(cls, field_name: str) -> str:
        """Ensures sensitive input identifiers are masked."""
        name_lower = (field_name or "").lower()
        if any(p in name_lower for p in cls.SENSITIVE_FIELD_PATTERNS):
            return "[REDACTED_SENSITIVE_FIELD]"
        return field_name[:255]

    @classmethod
    def log_issue(
        cls,
        db: Session,
        field_name: str,
        platform: str = "generic",
        application_id: Optional[int] = None,
        workflow_id: Optional[int] = None,
        field_label: Optional[str] = None,
        field_type: Optional[str] = None,
        issue_type: FieldIssueType = FieldIssueType.UNRECOGNIZED_FIELD,
        error_message: Optional[str] = None,
    ) -> ApplicationFieldIssue:
        safe_name = cls.sanitize_field_name(field_name)
        safe_label = cls.sanitize_field_name(field_label) if field_label else None

        issue = FeedbackRepository.create_field_issue(
            db=db,
            field_name=safe_name,
            platform=platform.lower() if platform else "generic",
            application_id=application_id,
            workflow_id=workflow_id,
            field_label=safe_label,
            field_type=field_type,
            issue_type=issue_type,
            error_message=error_message[:500] if error_message else None,
        )
        logger.info(f"Logged field issue on platform '{platform}': {issue_type.value} for field '{safe_name}'")
        return issue

    @classmethod
    def resolve_issue(cls, db: Session, issue_id: int) -> Optional[ApplicationFieldIssue]:
        return FeedbackRepository.resolve_field_issue(db, issue_id)

    @classmethod
    def list_issues(
        cls,
        db: Session,
        application_id: Optional[int] = None,
        platform: Optional[str] = None,
        issue_type: Optional[str] = None,
        resolved: Optional[bool] = None,
    ) -> List[ApplicationFieldIssue]:
        return FeedbackRepository.list_field_issues(
            db=db,
            application_id=application_id,
            platform=platform,
            issue_type=issue_type,
            resolved=resolved,
        )
