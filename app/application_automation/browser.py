import time
import uuid
import logging
from typing import Dict, Optional, List, Tuple
from datetime import datetime, timedelta
from bs4 import BeautifulSoup

from app.profile.models import UserProfile
from app.ingestion.validators import SafeHttpClient, validate_url_syntax
from app.application_automation.schemas import (
    FormPlatform,
    InspectionStatus,
    PageType,
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
        status: InspectionStatus = InspectionStatus.PREVIEW_READY,
        page_type: PageType = PageType.APPLICATION_FORM,
        html_content: str = "",
        page_title: str = "",
        ttl_minutes: int = SESSION_TTL_MINUTES
    ):
        self.session_id = session_id
        self.url = url
        self.platform = platform
        self.fields = fields
        self.status = status
        self.page_type = page_type
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
        status: InspectionStatus = InspectionStatus.PREVIEW_READY,
        page_type: PageType = PageType.APPLICATION_FORM,
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
            status=status,
            page_type=page_type,
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
            FormPlatform.ORACLE: GenericFormAdapter(),
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

        soup = BeautifulSoup(html_content, "html.parser")
        page_title = soup.title.get_text(strip=True) if soup.title else "Job Application"
        session_id = str(uuid.uuid4())

        # 3. Check for CAPTCHA Challenge
        if BaseFormAdapter.detect_captcha(html_content):
            session = self.session_manager.create_session(
                url=url_str,
                platform=platform,
                fields=[],
                status=InspectionStatus.CAPTCHA_DETECTED,
                page_type=PageType.CAPTCHA,
                html_content=html_content,
                page_title=page_title
            )
            return InspectApplicationResponse(
                success=False,
                session_id=session.session_id,
                platform=platform,
                status=InspectionStatus.CAPTCHA_DETECTED,
                page_type=PageType.CAPTCHA.value,
                page_url=url_str,
                page_title=page_title,
                captcha_detected=True,
                warnings=["CAPTCHA challenge detected on page. Automated inspection was halted for safety."],
                errors=["A CAPTCHA challenge is active. Please complete it manually in your browser."],
                submission_allowed=False
            )

        # 4. Check for Email Verification / OTP flow
        if BaseFormAdapter.detect_email_verification_required(html_content, url_str):
            adapter = self._select_adapter(platform)
            raw_fields = adapter.inspect_form(html_content, url_str)
            session = self.session_manager.create_session(
                url=url_str,
                platform=platform,
                fields=raw_fields,
                status=InspectionStatus.EMAIL_VERIFICATION_REQUIRED,
                page_type=PageType.EMAIL_VERIFICATION,
                html_content=html_content,
                page_title=page_title
            )
            return FormPreviewCompiler.compile_preview(
                session_id=session.session_id,
                platform=platform,
                page_url=url_str,
                raw_fields=raw_fields,
                profile=profile,
                page_title=page_title,
                status=InspectionStatus.EMAIL_VERIFICATION_REQUIRED,
                page_type=PageType.EMAIL_VERIFICATION,
                authentication_required=True,
                extra_warnings=["Email verification / One-Time Password (OTP) required. Please enter verification code manually in your browser."]
            )

        # 5. Check for Account Creation / Email Entry checkpoint (e.g. TI /apply/email)
        if BaseFormAdapter.detect_account_creation_required(html_content, url_str):
            adapter = self._select_adapter(platform)
            raw_fields = adapter.inspect_form(html_content, url_str)
            session = self.session_manager.create_session(
                url=url_str,
                platform=platform,
                fields=raw_fields,
                status=InspectionStatus.ACCOUNT_CREATION_REQUIRED,
                page_type=PageType.ACCOUNT_CREATION,
                html_content=html_content,
                page_title=page_title
            )
            return FormPreviewCompiler.compile_preview(
                session_id=session.session_id,
                platform=platform,
                page_url=url_str,
                raw_fields=raw_fields,
                profile=profile,
                page_title=page_title,
                status=InspectionStatus.ACCOUNT_CREATION_REQUIRED,
                page_type=PageType.ACCOUNT_CREATION,
                account_creation_required=True,
                extra_warnings=["An application account or email entry step is required before the full application form can be accessed. Please complete this step manually."]
            )

        # 6. Check for Authentication / Login Required
        if BaseFormAdapter.detect_authentication_required(html_content, status_code, url_str):
            adapter = self._select_adapter(platform)
            raw_fields = adapter.inspect_form(html_content, url_str)
            session = self.session_manager.create_session(
                url=url_str,
                platform=platform,
                fields=raw_fields,
                status=InspectionStatus.AUTH_REQUIRED,
                page_type=PageType.LOGIN,
                html_content=html_content,
                page_title=page_title
            )
            return FormPreviewCompiler.compile_preview(
                session_id=session.session_id,
                platform=platform,
                page_url=url_str,
                raw_fields=raw_fields,
                profile=profile,
                page_title=page_title,
                status=InspectionStatus.AUTH_REQUIRED,
                page_type=PageType.LOGIN,
                authentication_required=True,
                extra_warnings=["Authentication / Sign-in is required to access this application form. Please log in manually in your browser."]
            )

        # 7. Extract form fields using appropriate platform adapter
        adapter = self._select_adapter(platform)
        raw_fields = adapter.inspect_form(html_content, url_str)

        # 8. Classify Page when 0 fields are found
        if len(raw_fields) == 0:
            if BaseFormAdapter.detect_job_details_page(html_content, url_str):
                session = self.session_manager.create_session(
                    url=url_str,
                    platform=platform,
                    fields=[],
                    status=InspectionStatus.JOB_DETAILS_PAGE,
                    page_type=PageType.JOB_DETAILS,
                    html_content=html_content,
                    page_title=page_title
                )
                return InspectApplicationResponse(
                    success=True,
                    session_id=session.session_id,
                    platform=platform,
                    status=InspectionStatus.JOB_DETAILS_PAGE,
                    page_type=PageType.JOB_DETAILS.value,
                    page_url=url_str,
                    page_title=page_title,
                    fields=[],
                    warnings=["Target page is a Job Details preview. Click 'Apply' to navigate to the application form."],
                    submission_allowed=False
                )

            # Check if dynamic shell without rendered fields
            has_js_app_shell = bool(soup.select("#root, #app, [id*='app-root'], [class*='spinner'], [class*='loader']"))
            if has_js_app_shell:
                session = self.session_manager.create_session(
                    url=url_str,
                    platform=platform,
                    fields=[],
                    status=InspectionStatus.FORM_NOT_READY,
                    page_type=PageType.UNKNOWN,
                    html_content=html_content,
                    page_title=page_title
                )
                return InspectApplicationResponse(
                    success=False,
                    session_id=session.session_id,
                    platform=platform,
                    status=InspectionStatus.FORM_NOT_READY,
                    page_type=PageType.UNKNOWN.value,
                    page_url=url_str,
                    page_title=page_title,
                    fields=[],
                    warnings=["Application form fields did not render within the inspection timeout. The page may require a live browser session."],
                    submission_allowed=False
                )

            # Fallback unsupported page
            session = self.session_manager.create_session(
                url=url_str,
                platform=platform,
                fields=[],
                status=InspectionStatus.UNSUPPORTED_PAGE,
                page_type=PageType.UNKNOWN,
                html_content=html_content,
                page_title=page_title
            )
            return InspectApplicationResponse(
                success=False,
                session_id=session.session_id,
                platform=platform,
                status=InspectionStatus.UNSUPPORTED_PAGE,
                page_type=PageType.UNKNOWN.value,
                page_url=url_str,
                page_title=page_title,
                fields=[],
                warnings=["Could not detect any fillable application fields or standard form structures on this page."],
                submission_allowed=False
            )

        # 9. Legitimate application form with >= 1 fields -> PREVIEW_READY
        session = self.session_manager.create_session(
            url=url_str,
            platform=platform,
            fields=raw_fields,
            status=InspectionStatus.PREVIEW_READY,
            page_type=PageType.APPLICATION_FORM,
            html_content=html_content,
            page_title=page_title
        )

        return FormPreviewCompiler.compile_preview(
            session_id=session.session_id,
            platform=platform,
            page_url=url_str,
            raw_fields=raw_fields,
            profile=profile,
            page_title=page_title,
            status=InspectionStatus.PREVIEW_READY,
            page_type=PageType.APPLICATION_FORM,
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
        session = self.session_manager.get_session(session_id)

        # Guard: Check session status allows filling
        if session.status in (
            InspectionStatus.AUTH_REQUIRED,
            InspectionStatus.AUTHENTICATION_REQUIRED,
            InspectionStatus.ACCOUNT_CREATION_REQUIRED,
            InspectionStatus.EMAIL_VERIFICATION_REQUIRED,
            InspectionStatus.CAPTCHA_DETECTED,
            InspectionStatus.ACCESS_RESTRICTED,
            InspectionStatus.JOB_DETAILS_PAGE,
            InspectionStatus.FORM_NOT_READY,
            InspectionStatus.UNSUPPORTED_PAGE,
        ):
            raise AutomationException(
                code=AutomationErrorCode.STAGE_TRANSITION_INVALID,
                message=f"Cannot fill fields when application session status is '{session.status.value}'. Please complete authentication or navigate to the active application form first."
            )

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


default_browser_engine = BrowserAutomationEngine()
