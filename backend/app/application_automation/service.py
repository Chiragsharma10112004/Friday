import logging
from typing import Optional
from sqlalchemy.orm import Session

from app.profile.models import UserProfile
from app.applications.models import JobApplication
from app.application_automation.schemas import (
    InspectApplicationRequest,
    InspectApplicationResponse,
    FillApprovedFieldsRequest,
    FillApprovedFieldsResponse,
)
from app.application_automation.errors import AutomationErrorCode, AutomationException
from app.application_automation.browser import default_browser_engine

logger = logging.getLogger("friday.automation.service")


class ApplicationAutomationService:
    """
    Orchestration service for Browser-Assisted Job Application Form Automation (Phase 4).
    """

    @classmethod
    def _resolve_application_url(
        cls,
        request: InspectApplicationRequest,
        db: Session
    ) -> str:
        url = request.application_url

        if not url and request.application_id:
            job_app = db.query(JobApplication).filter(JobApplication.id == request.application_id).first()
            if not job_app:
                raise AutomationException(
                    code=AutomationErrorCode.APPLICATION_NOT_FOUND,
                    message=f"Job application with ID {request.application_id} not found in database."
                )
            url = job_app.job_url

        elif not url and request.normalized_job:
            url = request.normalized_job.source_url

        if not url or not url.strip():
            raise AutomationException(
                code=AutomationErrorCode.INVALID_APPLICATION_URL,
                message="A valid target application URL or application_id is required."
            )

        return url.strip()

    @classmethod
    def inspect_form(
        cls,
        request: InspectApplicationRequest,
        db: Session
    ) -> InspectApplicationResponse:
        url = cls._resolve_application_url(request, db)

        profile = db.query(UserProfile).first()
        if not profile:
            raise AutomationException(
                code=AutomationErrorCode.PROFILE_NOT_FOUND,
                message="Master candidate profile not found. Please create a profile before automating forms."
            )

        return default_browser_engine.inspect_application_page(
            url=url,
            profile=profile
        )

    @classmethod
    def refresh_inspection(
        cls,
        session_id: str,
        db: Session
    ) -> InspectApplicationResponse:
        """
        Re-inspect active session URL after manual authentication or account creation in browser.
        """
        session = default_browser_engine.session_manager.get_session(session_id)
        profile = db.query(UserProfile).first()
        if not profile:
            raise AutomationException(
                code=AutomationErrorCode.PROFILE_NOT_FOUND,
                message="Master candidate profile not found."
            )
        return default_browser_engine.inspect_application_page(
            url=session.url,
            profile=profile
        )

    @classmethod
    def fill_form(
        cls,
        request: FillApprovedFieldsRequest
    ) -> FillApprovedFieldsResponse:
        if not request.session_id:
            raise AutomationException(
                code=AutomationErrorCode.SESSION_NOT_FOUND,
                message="session_id is required to fill approved fields."
            )

        if not request.approved_field_ids and not request.custom_answers:
            raise AutomationException(
                code=AutomationErrorCode.FIELD_NOT_APPROVED,
                message="No fields were approved for automated filling."
            )

        return default_browser_engine.fill_approved_fields(
            session_id=request.session_id,
            approved_field_ids=request.approved_field_ids,
            custom_answers=request.custom_answers
        )


default_automation_service = ApplicationAutomationService()
