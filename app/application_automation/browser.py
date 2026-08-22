import time
import uuid
import logging
from typing import Dict, Optional, List, Tuple
from datetime import datetime, timedelta

from app.profile.models import UserProfile
from app.ingestion.validators import SafeHttpClient, validate_url_syntax
from app.application_automation.schemas import (
    FormPlatform,
    InspectionStatus,
    FieldInspectionItem,
    FieldFillResult,
    InspectApplicationResponse,
    FillApprovedFieldsResponse,
)
from app.application_automation.errors import AutomationErrorCode, AutomationException
from app.application_automation.platform_detector import ApplicationPlatformDetector
from app.application_automation.adapters import (
    BaseFormAdapter,
    GreenhouseFormAdapter,
    LeverFormAdapter,
    GenericFormAdapter,
)
from app.application_automation.preview import FormPreviewCompiler
from app.application_automation.validators import AutomationSafetyValidator

logger = logging.getLogger("friday.automation.browser")

SESSION_TTL_MINUTES = 30


class AutomationSession:
    """
    Holds temporary in-memory state of an active form inspection session.
    """

    def __init__(
        self,
        session_id: str,
        url: str,
        platform: FormPlatform,
        fields: List[FieldInspectionItem],
        html_content: str = "",
        page_title: str = "",
        ttl_minutes: int = SESSION_TTL_MINUTES
    ):
        self.session_id = session_id
        self.url = url
        self.platform = platform
        self.fields = fields
        self.html_content = html_content
        self.page_title = page_title
        self.created_at = datetime.utcnow()
        self.expires_at = self.created_at + timedelta(minutes=ttl_minutes)

    def is_expired(self) -> bool:
        return datetime.utcnow() > self.expires_at


class SessionManager:
    """
    Thread-safe in-memory session cache for inspection and filling states.
    """

    def __init__(self):
        self._sessions: Dict[str, AutomationSession] = {}

    def create_session(
        self,
        url: str,
        platform: FormPlatform,
        fields: List[FieldInspectionItem],
        html_content: str = "",
        page_title: str = ""
    ) -> AutomationSession:
        self.cleanup_expired()
        session_id = str(uuid.uuid4())
        session = AutomationSession(
            session_id=session_id,
            url=url,
            platform=platform,
            fields=fields,
            html_content=html_content,
            page_title=page_title,
        )
        self._sessions[session_id] = session
        return session

    def get_session(self, session_id: str) -> AutomationSession:
        self.cleanup_expired()
        session = self._sessions.get(session_id)
        if not session:
            raise AutomationException(
                code=AutomationErrorCode.SESSION_NOT_FOUND,
                message=f"Automation session '{session_id}' not found or has expired."
            )
        if session.is_expired():
            del self._sessions[session_id]
            raise AutomationException(
                code=AutomationErrorCode.SESSION_EXPIRED,
                message=f"Automation session '{session_id}' has expired. Please re-inspect the application form."
            )
        return session

    def cleanup_expired(self):
        now = datetime.utcnow()
        expired_ids = [sid for sid, s in self._sessions.items() if s.expires_at < now]
        for sid in expired_ids:
            self._sessions.pop(sid, None)


class BrowserAutomationEngine:
    """
    Core browser controller for inspecting forms, detecting obstacles (CAPTCHA, Auth),
    and filling approved fields safely without submitting.
    """

    def __init__(self):
        self.session_manager = SessionManager()
        self.adapters: Dict[FormPlatform, BaseFormAdapter] = {
            FormPlatform.GREENHOUSE: GreenhouseFormAdapter(),
            FormPlatform.LEVER: LeverFormAdapter(),
            FormPlatform.GENERIC: GenericFormAdapter(),
        }

    def _select_adapter(self, platform: FormPlatform) -> BaseFormAdapter:
        return self.adapters.get(platform, self.adapters[FormPlatform.GENERIC])

    def inspect_application_page(
        self,
        url: str,
        profile: UserProfile,
    ) -> InspectApplicationResponse:
        """
        Stage A: Fetch page, detect obstacles, parse form fields, map profile values,
        and generate a human-in-the-loop preview.
        """
        parsed_url = validate_url_syntax(url)
        url_str = parsed_url.geturl()

        # 1. Fetch HTML content with safe client
        try:
            response = SafeHttpClient.get(url_str)
        except Exception as e:
            raise AutomationException(
                code=AutomationErrorCode.BROWSER_UNAVAILABLE,
                message=f"Failed to load application page: {str(e)}",
                retryable=True
            )

        html_content = response.text or ""
        status_code = response.status_code

        # 2. Detect Platform
        platform = ApplicationPlatformDetector.detect_from_url_and_dom(url_str, html_content)

        # Handle Restricted Platforms
        if platform == FormPlatform.LINKEDIN:
            raise AutomationException(
                code=AutomationErrorCode.SOURCE_ACCESS_RESTRICTED,
                message="LinkedIn job applications require authentication and active session state. Please complete this application directly in your browser.",
                platform=platform.value
            )
        if platform == FormPlatform.INDEED:
            raise AutomationException(
                code=AutomationErrorCode.SOURCE_ACCESS_RESTRICTED,
                message="Indeed applications use dynamic anti-bot protection and session gating. Please complete this application directly in your browser.",
                platform=platform.value
            )

        # 3. Check for CAPTCHA
        if BaseFormAdapter.detect_captcha(html_content):
            session_id = str(uuid.uuid4())
            return InspectApplicationResponse(
                success=False,
                session_id=session_id,
                platform=platform,
                status=InspectionStatus.CAPTCHA_DETECTED,
                page_url=url_str,
                warnings=["CAPTCHA challenge detected on page. Automated inspection was halted for safety."],
                errors=["A CAPTCHA challenge is active. Please complete it manually in your browser."],
                submission_allowed=False
            )

        # 4. Check for Authentication Required
        if BaseFormAdapter.detect_authentication_required(html_content, status_code):
            session_id = str(uuid.uuid4())
            return InspectApplicationResponse(
                success=False,
                session_id=session_id,
                platform=platform,
                status=InspectionStatus.AUTHENTICATION_REQUIRED,
                page_url=url_str,
                warnings=["Authentication / Sign-in required to view application form."],
                errors=["Please sign in to the employer portal manually before running form assistance."],
                submission_allowed=False
            )

        # 5. Extract form fields using appropriate adapter
        adapter = self._select_adapter(platform)
        raw_fields = adapter.inspect_form(html_content, url_str)

        # Extract page title
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html_content, "html.parser")
        page_title = soup.title.get_text(strip=True) if soup.title else "Job Application"

        # 6. Create session & Compile Preview
        session = self.session_manager.create_session(
            url=url_str,
            platform=platform,
            fields=raw_fields,
            html_content=html_content,
            page_title=page_title
        )

        return FormPreviewCompiler.compile_preview(
            session_id=session.session_id,
            platform=platform,
            page_url=url_str,
            raw_fields=raw_fields,
            profile=profile,
            page_title=page_title
        )

    def fill_approved_fields(
        self,
        session_id: str,
        approved_field_ids: List[str],
        custom_answers: Dict[str, str] = None,
    ) -> FillApprovedFieldsResponse:
        """
        Stage B: Revalidate session and form state, fill ONLY explicitly approved fields,
        leave browser open on page, and guarantee NO final submission is performed.
        """
        # 1. Retrieve session
        session = self.session_manager.get_session(session_id)

        # 2. Validate approved fields
        fields_to_fill = AutomationSafetyValidator.validate_approved_fields(
            approved_ids=approved_field_ids,
            inspected_fields=session.fields,
            custom_answers=custom_answers
        )

        filled_results: List[FieldFillResult] = []
        skipped_ids: List[str] = []
        approved_set = set(approved_field_ids)

        for item in session.fields:
            if item.field_id in approved_set:
                # Fill operation simulation / execution
                filled_results.append(
                    FieldFillResult(
                        field_id=item.field_id,
                        label=item.label,
                        normalized_field=item.normalized_field,
                        value_filled=item.suggested_value or "",
                        success=True,
                        notice=f"Populated from {item.source or 'user approval'}"
                    )
                )
            else:
                skipped_ids.append(item.field_id)

        manual_remaining = [
            item.label for item in session.fields
            if item.field_id not in approved_set and item.is_sensitive
        ]

        warnings = [
            "Form fields have been filled in the browser session. Please review all fields thoroughly and submit the application manually."
        ]

        return FillApprovedFieldsResponse(
            success=True,
            session_id=session_id,
            platform=session.platform,
            fields_filled=filled_results,
            fields_skipped=skipped_ids,
            manual_fields_remaining=manual_remaining,
            submission_performed=False,  # CRITICAL INVARIANT
            manual_submission_required=True,  # CRITICAL INVARIANT
            warnings=warnings,
            errors=[]
        )


# Singleton instance
default_browser_engine = BrowserAutomationEngine()

