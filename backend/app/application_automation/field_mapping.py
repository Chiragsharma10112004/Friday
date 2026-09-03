import re
from typing import Optional, Tuple, List, Dict, Any

from app.profile.models import UserProfile
from app.application_automation.schemas import (
    FieldConfidence,
    FieldStatus,
    QuestionType,
)

FIELD_PATTERNS: Dict[str, List[re.Pattern]] = {
    "first_name": [
        re.compile(r"\b(first[\s_-]?name|given[\s_-]?name|fname)\b", re.I),
    ],
    "last_name": [
        re.compile(r"\b(last[\s_-]?name|family[\s_-]?name|surname|lname)\b", re.I),
    ],
    "full_name": [
        re.compile(r"\b(full[\s_-]?name|your[\s_-]?name|candidate[\s_-]?name|^name$)\b", re.I),
    ],
    "email": [
        re.compile(r"\b(email|email[\s_-]?address|e-mail)\b", re.I),
    ],
    "phone": [
        re.compile(r"\b(phone|phone[\s_-]?number|telephone|mobile|contact[\s_-]?number)\b", re.I),
    ],
    "location": [
        re.compile(r"\b(location|city|current[\s_-]?location|address|residence)\b", re.I),
    ],
    "linkedin_url": [
        re.compile(r"\b(linkedin|linked[\s_-]?in|linkedin[\s_-]?profile|linkedin[\s_-]?url)\b", re.I),
    ],
    "github_url": [
        re.compile(r"\b(github|git[\s_-]?hub|github[\s_-]?profile|github[\s_-]?url)\b", re.I),
    ],
    "portfolio_url": [
        re.compile(r"\b(portfolio|website|personal[\s_-]?website|portfolio[\s_-]?url|other[\s_-]?website)\b", re.I),
    ],
    "university": [
        re.compile(r"\b(university|school|college|institution|alma[\s_-]?mater)\b", re.I),
    ],
    "degree": [
        re.compile(r"\b(degree|qualification|highest[\s_-]?degree|education[\s_-]?level)\b", re.I),
    ],
    "branch": [
        re.compile(r"\b(branch|major|field[\s_-]?of[\s_-]?study|discipline|department)\b", re.I),
    ],
    "graduation_year": [
        re.compile(r"\b(graduation[\s_-]?year|grad[\s_-]?year|year[\s_-]?of[\s_-]?graduation|completion[\s_-]?year)\b", re.I),
    ],
    "cgpa": [
        re.compile(r"\b(cgpa|gpa|grade[\s_-]?point|percentage)\b", re.I),
    ],
    "work_authorization": [
        re.compile(r"\b(authorized[\s_-]?to[\s_-]?work|work[\s_-]?authorization|legally[\s_-]?authorized)\b", re.I),
    ],
    "sponsorship_required": [
        re.compile(r"\b(require[\s_-]?sponsorship|visa[\s_-]?sponsorship|future[\s_-]?sponsorship)\b", re.I),
    ],
    "headline": [
        re.compile(r"\b(headline|title|professional[\s_-]?title|current[\s_-]?title)\b", re.I),
    ],
    "summary": [
        re.compile(r"\b(summary|about[\s_-]?you|professional[\s_-]?summary|bio|introduction)\b", re.I),
    ],
    "resume": [
        re.compile(r"\b(resume|cv|curriculum[\s_-]?vitae|upload[\s_-]?resume)\b", re.I),
    ],
    "cover_letter": [
        re.compile(r"\b(cover[\s_-]?letter|letter|message[\s_-]?to[\s_-]?hiring[\s_-]?manager)\b", re.I),
    ],
}

# Sensitive / compliance / authentication questions
SENSITIVE_PATTERNS: List[re.Pattern] = [
    re.compile(r"\b(password|passcode|secret|credential|otp|one[\s_-]?time[\s_-]?password|pin|token)\b", re.I),
    re.compile(r"\b(gender|sex|sexual[\s_-]?orientation)\b", re.I),
    re.compile(r"\b(race|ethnicity|hispanic|latino|caucasian|african[\s_-]?american|asian)\b", re.I),
    re.compile(r"\b(disability|veteran|military[\s_-]?status|protected[\s_-]?veteran)\b", re.I),
    re.compile(r"\b(salary|compensation|expected[\s_-]?salary|desired[\s_-]?pay|hourly[\s_-]?rate)\b", re.I),
    re.compile(r"\b(criminal|felony|misdemeanor|background[\s_-]?check|convict)\b", re.I),
    re.compile(r"\b(security[\s_-]?clearance|citizenship|nationality|date[\s_-]?of[\s_-]?birth|dob)\b", re.I),
    re.compile(r"\b(equal[\s_-]?opportunity|eeo|voluntary[\s_-]?self[\s_-]?identification)\b", re.I),
    re.compile(r"\b(notice[\s_-]?period|availability|start[\s_-]?date)\b", re.I),
]


class FieldMapper:
    """
    Deterministic field normalizer and candidate profile attribute resolver.
    """

    @staticmethod
    def is_sensitive_question(text: str, control_type: QuestionType = QuestionType.TEXT) -> bool:
        if control_type == QuestionType.PASSWORD:
            return True
        return any(pattern.search(text) for pattern in SENSITIVE_PATTERNS)

    @classmethod
    def match_canonical_field(cls, label: str, html_name: str = "", control_type: QuestionType = QuestionType.TEXT) -> Optional[str]:
        # Password is never mapped to profile
        if control_type == QuestionType.PASSWORD:
            return None

        combined_text = f"{label} {html_name}".strip()

        if control_type == QuestionType.EMAIL and not any(kw in combined_text.lower() for kw in ["referrer", "friend", "manager"]):
            return "email"
        if control_type == QuestionType.TEL:
            return "phone"

        for field_name, patterns in FIELD_PATTERNS.items():
            for pat in patterns:
                if pat.search(combined_text):
                    return field_name

        return None

    @classmethod
    def resolve_candidate_value(
        cls,
        canonical_key: Optional[str],
        profile: UserProfile,
        label: str = "",
        html_name: str = "",
        control_type: QuestionType = QuestionType.TEXT,
    ) -> Tuple[Optional[str], Optional[str], FieldConfidence, FieldStatus, bool, Optional[str]]:
        combined_text = f"{label} {html_name}".strip()

        # 1. Sensitive questions / Password / Auth fields are ALWAYS MANUAL_REQUIRED
        if cls.is_sensitive_question(combined_text, control_type):
            notice = "Authentication, demographic, compensation, or compliance questions require manual review."
            if control_type == QuestionType.PASSWORD or "password" in combined_text.lower() or "otp" in combined_text.lower():
                notice = "Password and verification credentials must be completed manually in your browser."
            return (
                None,
                None,
                FieldConfidence.UNSUPPORTED,
                FieldStatus.MANUAL_REQUIRED,
                True,
                notice
            )

        if not canonical_key:
            return (
                None,
                None,
                FieldConfidence.UNSUPPORTED,
                FieldStatus.MANUAL_REQUIRED,
                False,
                "Custom question not mapped to candidate profile."
            )

        # 2. Map directly to UserProfile attributes
        value = None
        source = None
        confidence = FieldConfidence.HIGH
        status = FieldStatus.AUTO_FILL_READY
        notice = None

        if canonical_key == "first_name":
            value = profile.first_name
            source = "profile.first_name"
        elif canonical_key == "last_name":
            value = profile.last_name
            source = "profile.last_name"
        elif canonical_key == "full_name":
            first = profile.first_name or ""
            last = profile.last_name or ""
            value = f"{first} {last}".strip() or None
            source = "profile.full_name"
        elif canonical_key == "email":
            value = profile.email
            source = "profile.email"
        elif canonical_key == "phone":
            value = profile.phone
            source = "profile.phone"
        elif canonical_key == "location":
            value = profile.location
            source = "profile.location"
        elif canonical_key == "linkedin_url":
            value = profile.linkedin_url
            source = "profile.linkedin_url"
        elif canonical_key == "github_url":
            value = profile.github_url
            source = "profile.github_url"
        elif canonical_key == "portfolio_url":
            value = profile.portfolio_url
            source = "profile.portfolio_url"
        elif canonical_key == "university":
            value = profile.university
            source = "profile.university"
        elif canonical_key == "degree":
            value = profile.degree
            source = "profile.degree"
        elif canonical_key == "branch":
            value = profile.branch
            source = "profile.branch"
        elif canonical_key == "graduation_year":
            value = str(profile.graduation_year) if profile.graduation_year else None
            source = "profile.graduation_year"
        elif canonical_key == "cgpa":
            value = str(profile.cgpa) if profile.cgpa else None
            source = "profile.cgpa"
        elif canonical_key == "work_authorization":
            value = profile.work_authorization
            source = "profile.work_authorization"
            confidence = FieldConfidence.MEDIUM
            status = FieldStatus.APPROVAL_REQUIRED
            notice = "Please confirm work authorization answer."
        elif canonical_key == "sponsorship_required":
            value = profile.sponsorship_required
            source = "profile.sponsorship_required"
            confidence = FieldConfidence.MEDIUM
            status = FieldStatus.APPROVAL_REQUIRED
            notice = "Please confirm sponsorship answer."
        elif canonical_key == "resume":
            if profile.resume_path:
                value = profile.resume_path
                source = "profile.resume_path"
                confidence = FieldConfidence.MEDIUM
                status = FieldStatus.APPROVAL_REQUIRED
                notice = "Resume file upload requires confirmation."
            else:
                value = None
                source = None
                confidence = FieldConfidence.LOW
                status = FieldStatus.MANUAL_REQUIRED
                notice = "No resume file path configured in profile (ASSET_FILE_NOT_AVAILABLE)."
        elif canonical_key == "cover_letter":
            value = None
            source = None
            confidence = FieldConfidence.MEDIUM
            status = FieldStatus.APPROVAL_REQUIRED
            notice = "Cover letter text can be attached from Phase 3 assets."

        if not value or not str(value).strip():
            return (
                None,
                None,
                FieldConfidence.LOW,
                FieldStatus.MANUAL_REQUIRED,
                False,
                f"Candidate fact '{canonical_key}' is not populated in master profile."
            )

        return (str(value), source, confidence, status, False, notice)
