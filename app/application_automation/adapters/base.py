from abc import ABC, abstractmethod
from typing import List, Optional
from bs4 import BeautifulSoup

from app.application_automation.schemas import (
    FormPlatform,
    FieldInspectionItem,
    QuestionType,
    FieldConfidence,
    FieldStatus,
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
        Detect presence of CAPTCHA challenges (reCAPTCHA, hCaptcha, Turnstile, Arkose).
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
        ]
        return any(sig in lower for sig in captcha_signatures)

    @staticmethod
    def detect_authentication_required(html_content: str, status_code: int = 200) -> bool:
        """
        Detect if the application page requires candidate login/authentication.
        """
        if status_code in (401, 403):
            return True

        if not html_content:
            return False

        lower = html_content.lower()
        auth_signatures = [
            "sign in to apply",
            "log in to apply",
            "create an account to continue",
            "enter your password",
            "login_form",
            "auth0",
        ]
        return any(sig in lower for sig in auth_signatures)

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

