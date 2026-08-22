import unittest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from app.main import app
from app.memory.database import SessionLocal
from app.profile.models import UserProfile
from app.applications.models import JobApplication
from app.application_automation.schemas import (
    FormPlatform,
    FieldConfidence,
    FieldStatus,
    QuestionType,
    InspectionStatus,
    PageType,
    InspectApplicationRequest,
    InspectApplicationResponse,
    FillApprovedFieldsRequest,
    FillApprovedFieldsResponse,
)
from app.application_automation.errors import AutomationErrorCode, AutomationException
from app.application_automation.service import default_automation_service
from app.application_automation.browser import default_browser_engine
from app.application_automation.adapters.greenhouse import GreenhouseFormAdapter
from app.application_automation.adapters.lever import LeverFormAdapter
from app.application_automation.adapters.generic import GenericFormAdapter
from app.application_automation.field_mapping import FieldMapper
from app.application_automation.validators import AutomationSafetyValidator


class Phase4AutomationTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        cls.db = SessionLocal()

        profile = cls.db.query(UserProfile).first()
        if not profile:
            profile = UserProfile(
                first_name="Chirag",
                last_name="Sharma",
                email="chirag@example.com",
                phone="+1-555-0199",
                location="San Francisco, CA",
                linkedin_url="https://linkedin.com/in/chiragsharma",
                github_url="https://github.com/chiragsharma",
                portfolio_url="https://chiragsharma.dev",
                headline="Senior AI Backend Engineer",
                summary="Experienced backend engineer specializing in Python, FastAPI, and GenAI applications.",
                university="GITAM University",
                degree="B.Tech",
                branch="Computer Science",
                graduation_year=2024,
                cgpa="3.8",
                skills="Python, FastAPI, SQLAlchemy, PostgreSQL, Docker, GenAI, LLMs",
                work_authorization="Authorized to work in US/India",
                sponsorship_required="No"
            )
            cls.db.add(profile)
            cls.db.commit()
            cls.db.refresh(profile)
        cls.profile = profile

        job_app = cls.db.query(JobApplication).filter(JobApplication.company == "AutomationCorp").first()
        if not job_app:
            job_app = JobApplication(
                company="AutomationCorp",
                role="Senior Platform Engineer",
                job_url="https://boards.greenhouse.io/automationcorp/jobs/101",
                job_description="Seeking a Senior Platform Engineer.",
                match_score=92,
                recommendation="APPLY",
                status="NOT_APPLIED"
            )
            cls.db.add(job_app)
            cls.db.commit()
            cls.db.refresh(job_app)
        cls.job_app = job_app

    @classmethod
    def tearDownClass(cls):
        cls.db.close()

    def _get_sample_greenhouse_html(self):
        return """
        <html>
        <head><title>Senior Platform Engineer at AutomationCorp</title></head>
        <body>
            <form id="application_form" action="/apply">
                <div class="field">
                    <label for="first_name">First Name *</label>
                    <input type="text" id="first_name" name="first_name" required />
                </div>
                <div class="field">
                    <label for="last_name">Last Name *</label>
                    <input type="text" id="last_name" name="last_name" required />
                </div>
                <div class="field">
                    <label for="email">Email *</label>
                    <input type="email" id="email" name="email" required />
                </div>
                <div class="field">
                    <label for="phone">Phone *</label>
                    <input type="tel" id="phone" name="phone" />
                </div>
                <div class="field">
                    <label for="job_application_location">Location</label>
                    <input type="text" id="job_application_location" name="job_application[location]" />
                </div>
                <div class="field">
                    <label for="urls_linkedin">LinkedIn Profile</label>
                    <input type="text" id="urls_linkedin" name="job_application[urls][LinkedIn]" />
                </div>
                <div class="field">
                    <label for="urls_github">GitHub Profile</label>
                    <input type="text" id="urls_github" name="job_application[urls][GitHub]" />
                </div>
                <div class="field">
                    <label for="work_auth">Are you legally authorized to work in the US?</label>
                    <select id="work_auth" name="job_application[answers][1]">
                        <option value="">-- Please select --</option>
                        <option value="yes">Yes</option>
                        <option value="no">No</option>
                    </select>
                </div>
                <div class="field">
                    <label for="gender">Gender (Voluntary EEO)</label>
                    <select id="gender" name="job_application[gender]">
                        <option value="decline">Decline to self-identify</option>
                    </select>
                </div>
                <div class="field">
                    <label for="expected_salary">Desired Compensation / Salary</label>
                    <input type="text" id="expected_salary" name="job_application[salary]" />
                </div>
                <div class="field">
                    <button type="submit" id="submit_app">Submit Application</button>
                </div>
            </form>
        </body>
        </html>
        """

    def _get_sample_lever_html(self):
        return """
        <html>
        <head><title>Full Stack Engineer at Figma</title></head>
        <body>
            <form class="application-form" action="/apply">
                <div class="application-question">
                    <label class="application-label">Full Name ✱</label>
                    <input type="text" name="name" id="name" />
                </div>
                <div class="application-question">
                    <label class="application-label">Email ✱</label>
                    <input type="email" name="email" id="email" />
                </div>
                <div class="application-question">
                    <label class="application-label">Phone</label>
                    <input type="tel" name="phone" id="phone" />
                </div>
                <div class="application-question">
                    <label class="application-label">LinkedIn URL</label>
                    <input type="text" name="urls[LinkedIn]" id="urls_linkedin" />
                </div>
                <button type="submit" class="postings-btn">Submit Application</button>
            </form>
        </body>
        </html>
        """

    def _get_sample_ti_apply_email_html(self):
        return """
        <html>
        <head><title>Texas Instruments Careers - Candidate Portal</title></head>
        <body>
            <div class="cx-portal-container">
                <h2>Start Your Application</h2>
                <p>Enter your email to apply or create a candidate account.</p>
                <form action="/en/sites/CX/jobs/preview/25016856/apply/email" method="POST">
                    <label for="candidate_email">Email Address</label>
                    <input type="email" id="candidate_email" name="email" placeholder="name@domain.com" required />
                    <button type="submit">Continue with email</button>
                </form>
            </div>
        </body>
        </html>
        """

    def _get_sample_job_details_preview_html(self):
        return """
        <html>
        <head><title>Senior Systems Engineer - Texas Instruments</title></head>
        <body>
            <div class="job-header">
                <h1>Senior Systems Engineer</h1>
                <a href="/en/sites/CX/jobs/preview/25016856/apply/email" class="apply-btn">Apply Now</a>
            </div>
            <div class="job-description">
                <h2>Job Description</h2>
                <p>Texas Instruments is seeking a talented engineer...</p>
                <h2>Responsibilities</h2>
                <p>Design analog and embedded systems...</p>
            </div>
        </body>
        </html>
        """

    def _get_sample_login_page_html(self):
        return """
        <html>
        <head><title>Candidate Sign In - Employer Portal</title></head>
        <body>
            <form action="/login" method="POST">
                <h2>Sign In to Apply</h2>
                <label for="user_email">Email</label>
                <input type="email" id="user_email" name="username" />
                <label for="user_pass">Password</label>
                <input type="password" id="user_pass" name="password" autocomplete="current-password" />
                <button type="submit">Sign In</button>
            </form>
        </body>
        </html>
        """

    def _get_sample_otp_verification_html(self):
        return """
        <html>
        <head><title>Email Verification</title></head>
        <body>
            <form action="/verify-otp" method="POST">
                <h2>Verify Your Email</h2>
                <p>We sent a 6-digit one-time password (OTP) to your email.</p>
                <label for="otp_code">Enter Verification Code</label>
                <input type="text" id="otp_code" name="otp" placeholder="123456" />
                <button type="submit">Verify Code</button>
            </form>
        </body>
        </html>
        """

    # ==========================================
    # 1. Existing Platform Tests (Greenhouse & Lever)
    # ==========================================

    @patch("app.application_automation.browser.SafeHttpClient.get")
    def test_01_greenhouse_form_inspection_and_high_confidence_mapping(self, mock_http):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = self._get_sample_greenhouse_html()
        mock_http.return_value = mock_resp

        req = InspectApplicationRequest(application_url="https://boards.greenhouse.io/automationcorp/jobs/101")
        res: InspectApplicationResponse = default_automation_service.inspect_form(req, self.db)

        self.assertTrue(res.success)
        self.assertEqual(res.platform, FormPlatform.GREENHOUSE)
        self.assertEqual(res.status, InspectionStatus.PREVIEW_READY)
        self.assertFalse(res.submission_allowed)
        self.assertGreater(res.auto_fill_ready_count, 0)
        self.assertGreater(res.manual_required_count, 0)

        fields_by_key = {f.normalized_field: f for f in res.fields if f.normalized_field}
        self.assertIn("first_name", fields_by_key)
        self.assertEqual(fields_by_key["first_name"].suggested_value, self.profile.first_name)
        self.assertEqual(fields_by_key["first_name"].confidence, FieldConfidence.HIGH)
        self.assertEqual(fields_by_key["first_name"].status, FieldStatus.AUTO_FILL_READY)

        self.assertIn("email", fields_by_key)
        self.assertEqual(fields_by_key["email"].suggested_value, self.profile.email)
        self.assertEqual(fields_by_key["email"].confidence, FieldConfidence.HIGH)

    @patch("app.application_automation.browser.SafeHttpClient.get")
    def test_02_lever_form_inspection_and_full_name_mapping(self, mock_http):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = self._get_sample_lever_html()
        mock_http.return_value = mock_resp

        req = InspectApplicationRequest(application_url="https://jobs.lever.co/figma/123-abc")
        res = default_automation_service.inspect_form(req, self.db)

        self.assertTrue(res.success)
        self.assertEqual(res.platform, FormPlatform.LEVER)
        
        fields_by_key = {f.normalized_field: f for f in res.fields if f.normalized_field}
        self.assertIn("full_name", fields_by_key)
        expected_full_name = f"{self.profile.first_name} {self.profile.last_name}".strip()
        self.assertEqual(fields_by_key["full_name"].suggested_value, expected_full_name)
        self.assertEqual(fields_by_key["full_name"].status, FieldStatus.AUTO_FILL_READY)

    # ==========================================
    # 2. Sensitive Questions (MANUAL_REQUIRED)
    # ==========================================

    @patch("app.application_automation.browser.SafeHttpClient.get")
    def test_03_sensitive_questions_flagged_as_manual_required(self, mock_http):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = self._get_sample_greenhouse_html()
        mock_http.return_value = mock_resp

        req = InspectApplicationRequest(application_url="https://boards.greenhouse.io/automationcorp/jobs/101")
        res = default_automation_service.inspect_form(req, self.db)

        sensitive_fields = [f for f in res.fields if f.is_sensitive]
        self.assertGreater(len(sensitive_fields), 0)
        for sf in sensitive_fields:
            self.assertEqual(sf.status, FieldStatus.MANUAL_REQUIRED)
            self.assertTrue(sf.requires_approval)

    # ==========================================
    # 3. Restricted Platforms (LinkedIn & Indeed)
    # ==========================================

    def test_04_restricted_platform_linkedin_handling(self):
        req = InspectApplicationRequest(application_url="https://www.linkedin.com/jobs/view/999")
        with self.assertRaises(AutomationException) as ctx:
            default_automation_service.inspect_form(req, self.db)
        self.assertEqual(ctx.exception.code, AutomationErrorCode.SOURCE_ACCESS_RESTRICTED)

    def test_05_restricted_platform_indeed_handling(self):
        req = InspectApplicationRequest(application_url="https://indeed.com/viewjob?jk=123")
        with self.assertRaises(AutomationException) as ctx:
            default_automation_service.inspect_form(req, self.db)
        self.assertEqual(ctx.exception.code, AutomationErrorCode.SOURCE_ACCESS_RESTRICTED)

    # ==========================================
    # 4. CAPTCHA Obstacles
    # ==========================================

    @patch("app.application_automation.browser.SafeHttpClient.get")
    def test_06_captcha_detection_causes_safe_stop(self, mock_http):
        captcha_html = """
        <html>
        <body>
            <div class="g-recaptcha" data-sitekey="6Lc_sample"></div>
            <form><input name="name" /></form>
        </body>
        </html>
        """
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = captcha_html
        mock_http.return_value = mock_resp

        req = InspectApplicationRequest(application_url="https://careers.example.com/apply")
        res = default_automation_service.inspect_form(req, self.db)

        self.assertFalse(res.success)
        self.assertEqual(res.status, InspectionStatus.CAPTCHA_DETECTED)
        self.assertTrue(res.captcha_detected)
        self.assertIn("CAPTCHA challenge detected", res.warnings[0])

    # ==========================================
    # 5. TI Regression Check & Account Creation Flow
    # ==========================================

    @patch("app.application_automation.browser.SafeHttpClient.get")
    def test_07_texas_instruments_apply_email_account_creation_detection(self, mock_http):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = self._get_sample_ti_apply_email_html()
        mock_http.return_value = mock_resp

        req = InspectApplicationRequest(application_url="https://careers.ti.com/en/sites/CX/jobs/preview/25016856/apply/email")
        res = default_automation_service.inspect_form(req, self.db)

        self.assertEqual(res.platform, FormPlatform.ORACLE)
        self.assertEqual(res.status, InspectionStatus.ACCOUNT_CREATION_REQUIRED)
        self.assertEqual(res.page_type, PageType.ACCOUNT_CREATION.value)
        self.assertTrue(res.account_creation_required)
        self.assertNotEqual(res.status, InspectionStatus.PREVIEW_READY)
        self.assertFalse(res.submission_allowed)

    # ==========================================
    # 6. Job Details Preview Page (0 fields)
    # ==========================================

    @patch("app.application_automation.browser.SafeHttpClient.get")
    def test_08_job_details_page_classification(self, mock_http):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = self._get_sample_job_details_preview_html()
        mock_http.return_value = mock_resp

        req = InspectApplicationRequest(application_url="https://careers.ti.com/en/sites/CX/jobs/preview/25016856/")
        res = default_automation_service.inspect_form(req, self.db)

        self.assertEqual(res.status, InspectionStatus.JOB_DETAILS_PAGE)
        self.assertEqual(res.page_type, PageType.JOB_DETAILS.value)
        self.assertEqual(len(res.fields), 0)
        self.assertNotEqual(res.status, InspectionStatus.PREVIEW_READY)

    # ==========================================
    # 7. Authentication / Login Page Detection
    # ==========================================

    @patch("app.application_automation.browser.SafeHttpClient.get")
    def test_09_login_page_detection_and_password_safety(self, mock_http):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = self._get_sample_login_page_html()
        mock_http.return_value = mock_resp

        req = InspectApplicationRequest(application_url="https://careers.example.com/login")
        res = default_automation_service.inspect_form(req, self.db)

        self.assertEqual(res.status, InspectionStatus.AUTH_REQUIRED)
        self.assertEqual(res.page_type, PageType.LOGIN.value)
        self.assertTrue(res.authentication_required)

        # Check password field is strictly MANUAL_REQUIRED and sensitive
        for f in res.fields:
            if f.control_type == QuestionType.PASSWORD or "password" in f.label.lower():
                self.assertEqual(f.status, FieldStatus.MANUAL_REQUIRED)
                self.assertTrue(f.is_sensitive)
                self.assertIsNone(f.suggested_value)

    # ==========================================
    # 8. OTP / Email Verification Detection
    # ==========================================

    @patch("app.application_automation.browser.SafeHttpClient.get")
    def test_10_otp_email_verification_detection(self, mock_http):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = self._get_sample_otp_verification_html()
        mock_http.return_value = mock_resp

        req = InspectApplicationRequest(application_url="https://careers.example.com/verify-email")
        res = default_automation_service.inspect_form(req, self.db)

        self.assertEqual(res.status, InspectionStatus.EMAIL_VERIFICATION_REQUIRED)
        self.assertEqual(res.page_type, PageType.EMAIL_VERIFICATION.value)
        self.assertTrue(res.authentication_required)

    # ==========================================
    # 9. Fill Endpoint Safety & Blocking Invalid States
    # ==========================================

    @patch("app.application_automation.browser.SafeHttpClient.get")
    def test_11_fill_approved_fields_success_on_preview_ready(self, mock_http):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = self._get_sample_greenhouse_html()
        mock_http.return_value = mock_resp

        insp_req = InspectApplicationRequest(application_url="https://boards.greenhouse.io/automationcorp/jobs/101")
        insp_res = default_automation_service.inspect_form(insp_req, self.db)

        approved = ["#first_name", "#email"]
        fill_req = FillApprovedFieldsRequest(
            session_id=insp_res.session_id,
            approved_field_ids=approved
        )
        fill_res: FillApprovedFieldsResponse = default_automation_service.fill_form(fill_req)

        self.assertTrue(fill_res.success)
        self.assertEqual(len(fill_res.fields_filled), 2)
        self.assertFalse(fill_res.submission_performed)
        self.assertTrue(fill_res.manual_submission_required)

    @patch("app.application_automation.browser.SafeHttpClient.get")
    def test_12_fill_blocked_on_auth_or_account_creation_checkpoint(self, mock_http):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = self._get_sample_ti_apply_email_html()
        mock_http.return_value = mock_resp

        insp_req = InspectApplicationRequest(application_url="https://careers.ti.com/en/sites/CX/jobs/preview/25016856/apply/email")
        insp_res = default_automation_service.inspect_form(insp_req, self.db)

        fill_req = FillApprovedFieldsRequest(
            session_id=insp_res.session_id,
            approved_field_ids=["#candidate_email"]
        )
        with self.assertRaises(AutomationException) as ctx:
            default_automation_service.fill_form(fill_req)
        self.assertEqual(ctx.exception.code, AutomationErrorCode.STAGE_TRANSITION_INVALID)

    def test_13_fill_blocked_if_no_fields_approved(self):
        fill_req = FillApprovedFieldsRequest(
            session_id="dummy-session",
            approved_field_ids=[]
        )
        with self.assertRaises(AutomationException) as ctx:
            default_automation_service.fill_form(fill_req)
        self.assertEqual(ctx.exception.code, AutomationErrorCode.FIELD_NOT_APPROVED)

    def test_14_submission_action_strictly_forbidden(self):
        with self.assertRaises(AutomationException) as ctx:
            AutomationSafetyValidator.assert_no_submit_action("#submit_button", "Submit Application")
        self.assertEqual(ctx.exception.code, AutomationErrorCode.SUBMISSION_BLOCKED)

    # ==========================================
    # 10. HTTP API Endpoints & Refresh Support
    # ==========================================

    @patch("app.application_automation.browser.SafeHttpClient.get")
    def test_15_post_inspect_and_refresh_endpoints(self, mock_http):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = self._get_sample_greenhouse_html()
        mock_http.return_value = mock_resp

        # 1. POST /application-automation/inspect
        payload = {"application_url": "https://boards.greenhouse.io/automationcorp/jobs/101"}
        resp = self.client.post("/application-automation/inspect", json=payload)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data["success"])
        session_id = data["session_id"]

        # 2. POST /application-automation/inspect/{id}/refresh
        refresh_resp = self.client.post(f"/application-automation/inspect/{session_id}/refresh")
        self.assertEqual(refresh_resp.status_code, 200)
        refresh_data = refresh_resp.json()
        self.assertTrue(refresh_data["success"])
        self.assertEqual(refresh_data["status"], InspectionStatus.PREVIEW_READY)


if __name__ == "__main__":
    unittest.main()
