import re
from abc import ABC, abstractmethod
from typing import List, Optional, Tuple
from bs4 import BeautifulSoup

from app.application_automation.schemas import (
    FormPlatform,
    FieldInspectionItem,
    QuestionType,
    InspectionStatus,
    PageType,
)


class BaseFormAdapter(ABC):
    """
    Abstract adapter for inspecting, parsing, and classifying HTML job application forms.
    """

    @property
    @abstractmethod
    def platform(self) -> FormPlatform:
        pass

    @abstractmethod
    def inspect_form(self, html_content: str, url: str) -> List[FieldInspectionItem]:
        """
        Parse visible form controls and return raw FieldInspectionItems.
        """
        pass

    @staticmethod
    def detect_captcha(html_content: str) -> bool:
        """
        Detect presence of CAPTCHA challenges (reCAPTCHA, hCaptcha, Turnstile, Arkose, Cloudflare).
        """
        if not html_content:
            return False

        lower = html_content.lower()
        captcha_signatures = [
            "g-recaptcha",
            "recaptcha/api",
            "hcaptcha",
            "cf-turnstile",
            "arkoselabs",
            "geetest",
            "datadome",
            "challenge-running",
            "verify you are human",
            "just a moment...",
            "please enable cookies and reload the page",
        ]
        return any(sig in lower for sig in captcha_signatures)

    @staticmethod
    def detect_authentication_required(html_content: str, status_code: int = 200, url: str = "") -> bool:
        """
        Detect if the page requires existing user login/authentication credentials.
        """
        if status_code in (401, 403):
            return True

        if not html_content and not url:
            return False

        lower_url = (url or "").lower()
        if any(auth_path in lower_url for auth_path in ["/login", "/signin", "/sign-in", "/auth/login"]):
            return True

        lower_html = (html_content or "").lower()
        
        # Password field is a strong signal for login / authentication
        if 'type="password"' in lower_html or "type='password'" in lower_html or 'autocomplete="current-password"' in lower_html:
            return True

        auth_text_signatures = [
            "sign in to apply",
            "log in to apply",
            "enter your password",
            "login_form",
            "candidate sign in",
            "existing user login",
            "sign in with your account",
        ]
        return any(sig in lower_html for sig in auth_text_signatures)

    @staticmethod
    def detect_account_creation_required(html_content: str, url: str = "") -> bool:
        """
        Detect if the page requires entering email or creating a candidate profile before form access.
        """
        lower_url = (url or "").lower()
        if any(sig in lower_url for sig in ["/apply/email", "/register", "/signup", "/sign-up", "/create-account", "/new-candidate"]):
            return True

        lower_html = (html_content or "").lower()
        creation_text_signatures = [
            "enter your email to apply",
            "create an account to continue",
            "create account to apply",
            "create candidate account",
            "create a profile to apply",
            "continue with email",
            "start your application with your email",
            "new candidate registration",
            "register to apply",
        ]
        return any(sig in lower_html for sig in creation_text_signatures)

    @staticmethod
    def detect_email_verification_required(html_content: str, url: str = "") -> bool:
        """
        Detect if an OTP / verification code is requested.
        """
        lower_url = (url or "").lower()
        if any(sig in lower_url for sig in ["/verify-email", "/verify-otp", "/otp", "/enter-code"]):
            return True

        lower_html = (html_content or "").lower()
        otp_signatures = [
            "verify your email",
            "one-time password",
            "enter the code sent to",
            "enter verification code",
            "enter the 6-digit code",
            "one-time passcode",
            "we sent a verification code",
        ]
        return any(sig in lower_html for sig in otp_signatures)

    @staticmethod
    def detect_job_details_page(html_content: str, url: str = "") -> bool:
        """
        Detect if page is a job description/preview page rather than an active application form.
        """
        if not html_content:
            return False

        lower_url = (url or "").lower()
        lower_html = html_content.lower()

        # URL preview pattern
        if "/jobs/preview/" in lower_url or "/job-preview" in lower_url:
            return True

        has_apply_button = any(btn in lower_html for btn in ["apply now", "apply for this job", "start application", "submit application now"])
        has_jd_headings = any(hd in lower_html for hd in ["job description", "responsibilities", "qualifications", "about the role", "what you'll do", "requirements"])

        return has_apply_button and has_jd_headings

    @staticmethod
    def determine_control_type(tag_name: str, input_type: str = "") -> QuestionType:
        tag = tag_name.lower()
        inp_type = input_type.lower()

        if tag == "textarea":
            return QuestionType.TEXTAREA
        if tag == "select":
            return QuestionType.SELECT

        if tag == "input":
            if inp_type == "email":
                return QuestionType.EMAIL
            if inp_type in ("tel", "phone"):
                return QuestionType.TEL
            if inp_type == "password":
                return QuestionType.PASSWORD
            if inp_type == "radio":
                return QuestionType.RADIO
            if inp_type == "checkbox":
                return QuestionType.CHECKBOX
            if inp_type == "file":
                return QuestionType.FILE
            if inp_type == "date":
                return QuestionType.DATE
            return QuestionType.TEXT

        return QuestionType.UNKNOWN
