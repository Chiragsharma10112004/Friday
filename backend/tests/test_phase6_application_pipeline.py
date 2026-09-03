import unittest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient

from app.main import app
from app.memory.database import SessionLocal
from app.profile.models import UserProfile
from app.job_discovery.models import DiscoveredOpportunity
from app.application_pipeline.models import (
    TrackedApplication,
    ApplicationTimelineEvent,
    ApplicationInterview,
    ApplicationStatusHistory,
)
from app.application_pipeline.schemas import (
    ApplicationStatus,
    ApplicationPriority,
    ReferralStatus,
    FollowUpStatus,
    InterviewStage,
    InterviewMode,
    InterviewStatus,
    CreateApplicationRequest,
    UpdateApplicationRequest,
    ApplicationStatusTransitionRequest,
    MarkAppliedRequest,
    AddNoteRequest,
    ReferralRequest,
    FollowUpRequest,
    InterviewCreateRequest,
    InterviewUpdateRequest,
    ApplicationFilterParams,
)
from app.application_pipeline.errors import PipelineErrorCode, PipelineException
from app.application_pipeline.service import default_pipeline_service
from app.application_pipeline.reminders import FollowUpManager


class Phase6ApplicationPipelineTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        cls.db = SessionLocal()

        # Clean Phase 6 test tables for clean isolated test runs
        cls.db.query(ApplicationStatusHistory).delete()
        cls.db.query(ApplicationInterview).delete()
        cls.db.query(ApplicationTimelineEvent).delete()
        cls.db.query(TrackedApplication).delete()
        cls.db.commit()

        # Ensure candidate profile exists
        profile = cls.db.query(UserProfile).first()
        if not profile:
            profile = UserProfile(
                first_name="Chirag",
                last_name="Sharma",
                email="chirag@example.com",
                skills="Python, FastAPI, Docker, SQL, GenAI",
            )
            cls.db.add(profile)
            cls.db.commit()
            cls.db.refresh(profile)
        cls.profile = profile

        # Ensure a Phase 5 opportunity exists for testing conversions
        opp = cls.db.query(DiscoveredOpportunity).filter(DiscoveredOpportunity.external_id == "phase6-test-opp-1").first()
        if not opp:
            opp = DiscoveredOpportunity(
                external_id="phase6-test-opp-1",
                provider="greenhouse",
                source_url="https://boards.greenhouse.io/piper/jobs/9991",
                company="PiedPiper",
                title="Staff Backend Architect",
                location="San Francisco, CA (Remote)",
                is_remote=True,
                description="Architect distributed compression algorithms in Python.",
                match_score=95,
                recommendation="STRONG_MATCH",
                status="DISCOVERED"
            )
            cls.db.add(opp)
            cls.db.commit()
            cls.db.refresh(opp)
        cls.test_opp = opp

    @classmethod
    def tearDownClass(cls):
        cls.db.close()

    def setUp(self):
        # Refresh session
        self.db.rollback()

    # =========================================================
    # 1. Create Application (Manual & from Opportunity)
    # =========================================================

    def test_01_create_application_manually(self):
        req = CreateApplicationRequest(
            company="Hooli",
            role="Core Infrastructure Lead",
            source_url="https://hooli.com/careers/infra-101",
            source_platform="manual",
            job_id="hooli-infra-101",
            location="Mountain View, CA",
            workplace_type="Hybrid",
            employment_type="Full-time",
            priority=ApplicationPriority.HIGH,
            status=ApplicationStatus.DISCOVERED,
            match_score=88,
            recommendation="STRONG_MATCH",
            notes="Initial manual entry."
        )
        res = default_pipeline_service.create_application(req, self.db)
        self.assertIsNotNone(res.id)
        self.assertEqual(res.company, "Hooli")
        self.assertEqual(res.role, "Core Infrastructure Lead")
        self.assertEqual(res.priority, ApplicationPriority.HIGH)
        self.assertEqual(res.status, ApplicationStatus.DISCOVERED)

    def test_02_create_application_from_phase5_opportunity(self):
        res = default_pipeline_service.create_from_opportunity(self.test_opp.id, self.db)
        self.assertIsNotNone(res.id)
        self.assertEqual(res.company, "PiedPiper")
        self.assertEqual(res.role, "Staff Backend Architect")
        self.assertEqual(res.opportunity_id, self.test_opp.id)
        self.assertEqual(res.match_score, 95)
        self.assertEqual(res.status, ApplicationStatus.SAVED)

    # =========================================================
    # 2. Duplicate Detection
    # =========================================================

    def test_03_prevent_duplicate_application_by_job_id(self):
        req = CreateApplicationRequest(
            company="Hooli",
            role="Core Infrastructure Lead",
            job_id="hooli-infra-101",
        )
        with self.assertRaises(PipelineException) as ctx:
            default_pipeline_service.create_application(req, self.db)
        self.assertEqual(ctx.exception.code, PipelineErrorCode.DUPLICATE_APPLICATION)

    def test_04_prevent_duplicate_application_by_normalized_fallback(self):
        req = CreateApplicationRequest(
            company="Aviato Corp",
            role="Senior Systems Engineer",
            source_url="https://aviato.com/jobs/systems",
        )
        res = default_pipeline_service.create_application(req, self.db)
        self.assertIsNotNone(res.id)

        dup_req = CreateApplicationRequest(
            company="  aviato CORP  ",
            role="Senior Systems Engineer",
            source_url="https://aviato.com/jobs/systems",
        )
        with self.assertRaises(PipelineException) as ctx:
            default_pipeline_service.create_application(dup_req, self.db)
        self.assertEqual(ctx.exception.code, PipelineErrorCode.DUPLICATE_APPLICATION)

    # =========================================================
    # 3. Status Transitions & History
    # =========================================================

    def test_05_valid_lifecycle_transitions(self):
        req = CreateApplicationRequest(
            company="Initech",
            role="Database Administrator",
            source_url="https://initech.com/careers/dba",
            status=ApplicationStatus.DISCOVERED
        )
        app_res = default_pipeline_service.create_application(req, self.db)
        app_id = app_res.id

        # DISCOVERED -> SAVED
        t1 = default_pipeline_service.transition_status(
            app_id, ApplicationStatusTransitionRequest(status=ApplicationStatus.SAVED, note="Saved for review"), self.db
        )
        self.assertEqual(t1.status, ApplicationStatus.SAVED)
        self.assertIsNotNone(t1.date_saved)

        # SAVED -> ASSETS_READY
        t2 = default_pipeline_service.transition_status(
            app_id, ApplicationStatusTransitionRequest(status=ApplicationStatus.ASSETS_READY, note="Phase 3 assets synthesized"), self.db
        )
        self.assertEqual(t2.status, ApplicationStatus.ASSETS_READY)
        self.assertIsNotNone(t2.date_assets_generated)

        # ASSETS_READY -> READY_TO_APPLY
        t3 = default_pipeline_service.transition_status(
            app_id, ApplicationStatusTransitionRequest(status=ApplicationStatus.READY_TO_APPLY), self.db
        )
        self.assertEqual(t3.status, ApplicationStatus.READY_TO_APPLY)

        # READY_TO_APPLY -> APPLIED
        t4 = default_pipeline_service.transition_status(
            app_id, ApplicationStatusTransitionRequest(status=ApplicationStatus.APPLIED), self.db
        )
        self.assertEqual(t4.status, ApplicationStatus.APPLIED)
        self.assertIsNotNone(t4.date_applied)

        # APPLIED -> INTERVIEWING
        t5 = default_pipeline_service.transition_status(
            app_id, ApplicationStatusTransitionRequest(status=ApplicationStatus.INTERVIEWING), self.db
        )
        self.assertEqual(t5.status, ApplicationStatus.INTERVIEWING)

        # INTERVIEWING -> OFFER
        t6 = default_pipeline_service.transition_status(
            app_id, ApplicationStatusTransitionRequest(status=ApplicationStatus.OFFER), self.db
        )
        self.assertEqual(t6.status, ApplicationStatus.OFFER)
        self.assertIsNotNone(t6.offer_date)

        # OFFER -> CLOSED
        t7 = default_pipeline_service.transition_status(
            app_id, ApplicationStatusTransitionRequest(status=ApplicationStatus.CLOSED), self.db
        )
        self.assertEqual(t7.status, ApplicationStatus.CLOSED)

    def test_06_invalid_status_transition_rejected(self):
        req = CreateApplicationRequest(
            company="Massive Dynamic",
            role="Research Scientist",
            status=ApplicationStatus.SAVED
        )
        app_res = default_pipeline_service.create_application(req, self.db)

        # SAVED cannot jump directly to OFFER
        with self.assertRaises(PipelineException) as ctx:
            default_pipeline_service.transition_status(
                app_res.id, ApplicationStatusTransitionRequest(status=ApplicationStatus.OFFER), self.db
            )
        self.assertEqual(ctx.exception.code, PipelineErrorCode.INVALID_STATUS_TRANSITION)

    def test_07_closed_is_terminal_state(self):
        req = CreateApplicationRequest(
            company="Umbrella Corp",
            role="Bioinformatics Engineer",
            status=ApplicationStatus.WITHDRAWN
        )
        app_res = default_pipeline_service.create_application(req, self.db)
        default_pipeline_service.transition_status(
            app_res.id, ApplicationStatusTransitionRequest(status=ApplicationStatus.CLOSED), self.db
        )

        with self.assertRaises(PipelineException) as ctx:
            default_pipeline_service.transition_status(
                app_res.id, ApplicationStatusTransitionRequest(status=ApplicationStatus.SAVED), self.db
            )
        self.assertEqual(ctx.exception.code, PipelineErrorCode.INVALID_STATUS_TRANSITION)

    # =========================================================
    # 4. Mark Applied & Idempotency
    # =========================================================

    def test_08_mark_applied_and_idempotency(self):
        req = CreateApplicationRequest(
            company="Cyberdyne",
            role="AI Systems Architect",
            status=ApplicationStatus.READY_TO_APPLY
        )
        app_res = default_pipeline_service.create_application(req, self.db)

        applied_time = datetime.now(timezone.utc)
        res1 = default_pipeline_service.mark_applied(
            app_res.id, MarkAppliedRequest(applied_at=applied_time, note="Submitted via portal"), self.db
        )
        self.assertEqual(res1.status, ApplicationStatus.APPLIED)
        self.assertIsNotNone(res1.date_applied)

        res2 = default_pipeline_service.mark_applied(
            app_res.id, MarkAppliedRequest(note="Submitting again (idempotent)"), self.db
        )
        self.assertEqual(res2.status, ApplicationStatus.APPLIED)

    # =========================================================
    # 5. Timeline Events & Notes
    # =========================================================

    def test_09_timeline_audit_log(self):
        req = CreateApplicationRequest(
            company="Acme Corp",
            role="Platform Engineer",
            status=ApplicationStatus.DISCOVERED
        )
        app_res = default_pipeline_service.create_application(req, self.db)

        default_pipeline_service.add_note(app_res.id, AddNoteRequest(note="Spoke with hiring manager at meetup"), self.db)
        default_pipeline_service.transition_status(app_res.id, ApplicationStatusTransitionRequest(status=ApplicationStatus.SAVED), self.db)

        events = default_pipeline_service.get_timeline(app_res.id, self.db)
        self.assertGreaterEqual(len(events), 3)

        event_types = [e.event_type for e in events]
        self.assertIn("APPLICATION_CREATED", event_types)
        self.assertIn("NOTE_ADDED", event_types)
        self.assertIn("STATUS_CHANGED", event_types)

    # =========================================================
    # 6. Referral Tracking
    # =========================================================

    def test_10_referral_tracking(self):
        req = CreateApplicationRequest(
            company="Soylent Corp",
            role="FoodTech Automation Engineer",
            status=ApplicationStatus.DISCOVERED
        )
        app_res = default_pipeline_service.create_application(req, self.db)

        ref_req = ReferralRequest(
            status=ReferralStatus.REQUESTED,
            contact_name="Alice Smith",
            contact_identifier="alice@soylent.com",
            notes="Sent request via LinkedIn"
        )
        ref_res = default_pipeline_service.update_referral(app_res.id, ref_req, self.db)
        self.assertEqual(ref_res.referral_status, ReferralStatus.REQUESTED)
        self.assertEqual(ref_res.referral_contact_name, "Alice Smith")
        self.assertIsNotNone(ref_res.referral_requested_date)

        ref_req2 = ReferralRequest(
            status=ReferralStatus.REFERRED,
            contact_name="Alice Smith",
            notes="Referral submitted internally"
        )
        ref_res2 = default_pipeline_service.update_referral(app_res.id, ref_req2, self.db)
        self.assertEqual(ref_res2.referral_status, ReferralStatus.REFERRED)
        self.assertIsNotNone(ref_res2.referral_referred_date)

    # =========================================================
    # 7. Follow-Up Reminders & Calculations
    # =========================================================

    def test_11_follow_up_schedule_and_dynamic_status(self):
        req = CreateApplicationRequest(
            company="Stark Industries",
            role="Avionics AI Engineer",
            status=ApplicationStatus.APPLIED
        )
        app_res = default_pipeline_service.create_application(req, self.db)

        tomorrow = datetime.now(timezone.utc) + timedelta(days=1)
        fu_res = default_pipeline_service.schedule_follow_up(
            app_res.id, FollowUpRequest(next_follow_up_date=tomorrow, notes="Check recruiter reply"), self.db
        )
        self.assertEqual(fu_res.follow_up_status, FollowUpStatus.SCHEDULED)

        today = datetime.now(timezone.utc)
        yesterday = today - timedelta(days=1)

        status_today = FollowUpManager.calculate_follow_up_status(today)
        self.assertEqual(status_today, FollowUpStatus.DUE)

        status_past = FollowUpManager.calculate_follow_up_status(yesterday)
        self.assertEqual(status_past, FollowUpStatus.OVERDUE)

        comp_res = default_pipeline_service.complete_follow_up(app_res.id, self.db)
        self.assertEqual(comp_res.follow_up_status, FollowUpStatus.COMPLETED)

    # =========================================================
    # 8. Multiple Interview Rounds
    # =========================================================

    def test_12_multiple_interview_rounds_and_updates(self):
        req = CreateApplicationRequest(
            company="Wayne Enterprises",
            role="Autonomous Security Systems Lead",
            status=ApplicationStatus.APPLIED
        )
        app_res = default_pipeline_service.create_application(req, self.db)

        r1 = default_pipeline_service.create_interview(
            app_res.id,
            InterviewCreateRequest(
                stage=InterviewStage.SCREENING,
                scheduled_at=datetime.now(timezone.utc) + timedelta(days=2),
                mode=InterviewMode.PHONE,
                notes="Recruiter intro call"
            ),
            self.db
        )
        self.assertIsNotNone(r1.id)
        self.assertEqual(r1.stage, InterviewStage.SCREENING)

        r2 = default_pipeline_service.create_interview(
            app_res.id,
            InterviewCreateRequest(
                stage=InterviewStage.TECHNICAL_ROUND,
                scheduled_at=datetime.now(timezone.utc) + timedelta(days=5),
                mode=InterviewMode.VIDEO,
                meeting_url="https://meet.google.com/xyz-abc",
                notes="Live coding session"
            ),
            self.db
        )
        self.assertIsNotNone(r2.id)
        self.assertEqual(r2.stage, InterviewStage.TECHNICAL_ROUND)

        interview_list = default_pipeline_service.list_interviews(app_res.id, self.db)
        self.assertEqual(len(interview_list), 2)

        r1_updated = default_pipeline_service.update_interview(
            app_res.id,
            r1.id,
            InterviewUpdateRequest(status=InterviewStatus.COMPLETED, notes="Passed screening"),
            self.db
        )
        self.assertEqual(r1_updated.status, InterviewStatus.COMPLETED)

        with self.assertRaises(PipelineException) as ctx:
            default_pipeline_service.update_interview(
                app_res.id,
                999999,
                InterviewUpdateRequest(status=InterviewStatus.COMPLETED),
                self.db
            )
        self.assertEqual(ctx.exception.code, PipelineErrorCode.INTERVIEW_NOT_FOUND)

    # =========================================================
    # 9. Pipeline Summary & Listing Filters
    # =========================================================

    def test_13_pipeline_summary_and_application_filters(self):
        summary = default_pipeline_service.get_summary(self.db)
        self.assertGreater(summary.total_applications, 0)
        self.assertIn("status_counts", summary.model_dump())
        self.assertIn("priority_counts", summary.model_dump())
        self.assertIn("applications_by_company", summary.model_dump())

        list_res = default_pipeline_service.list_applications(
            ApplicationFilterParams(status=ApplicationStatus.DISCOVERED, page=1, page_size=10),
            self.db
        )
        for item in list_res.items:
            self.assertEqual(item.status, ApplicationStatus.DISCOVERED)

    # =========================================================
    # 10. HTTP REST API Endpoints Integration
    # =========================================================

    def test_14_api_endpoints_integration(self):
        # 1. POST /applications
        create_payload = {
            "company": "Tyrell Corp",
            "role": "Replicant Engineer",
            "priority": "HIGH",
            "status": "DISCOVERED",
            "job_id": "tyrell-101"
        }
        post_resp = self.client.post("/applications", json=create_payload)
        self.assertEqual(post_resp.status_code, 201)
        created_data = post_resp.json()
        app_id = created_data["id"]
        self.assertEqual(created_data["company"], "Tyrell Corp")

        # 2. GET /applications/{id}
        get_resp = self.client.get(f"/applications/{app_id}")
        self.assertEqual(get_resp.status_code, 200)
        self.assertEqual(get_resp.json()["id"], app_id)

        # 3. PATCH /applications/{id}
        patch_resp = self.client.patch(f"/applications/{app_id}", json={"priority": "URGENT", "notes": "Top target"})
        self.assertEqual(patch_resp.status_code, 200)
        self.assertEqual(patch_resp.json()["priority"], "URGENT")

        # 4. POST /applications/{id}/status
        status_resp = self.client.post(f"/applications/{app_id}/status", json={"status": "SAVED", "note": "Moved to saved"})
        self.assertEqual(status_resp.status_code, 200)
        self.assertEqual(status_resp.json()["status"], "SAVED")

        # 5. POST /applications/{id}/mark-applied
        applied_resp = self.client.post(f"/applications/{app_id}/mark-applied", json={"note": "Submitted application"})
        self.assertEqual(applied_resp.status_code, 200)
        self.assertEqual(applied_resp.json()["status"], "APPLIED")

        # 6. GET /applications/{id}/timeline
        timeline_resp = self.client.get(f"/applications/{app_id}/timeline")
        self.assertEqual(timeline_resp.status_code, 200)
        self.assertGreaterEqual(len(timeline_resp.json()), 3)

        # 7. GET /applications/summary
        summary_resp = self.client.get("/applications/summary")
        self.assertEqual(summary_resp.status_code, 200)
        self.assertIn("total_applications", summary_resp.json())

        # 8. GET /applications/dashboard (backward-compatible)
        dash_resp = self.client.get("/applications/dashboard")
        self.assertEqual(dash_resp.status_code, 200)
        self.assertIn("total_applications", dash_resp.json())

        # 9. GET /applications/follow-ups
        fu_resp = self.client.get("/applications/follow-ups")
        self.assertEqual(fu_resp.status_code, 200)
        self.assertIn("scheduled", fu_resp.json())

        # 10. GET /applications/999999 (404 check)
        err_resp = self.client.get("/applications/999999")
        self.assertEqual(err_resp.status_code, 404)

        # 11. POST /applications/from-opportunity/999999 (404 check)
        err_opp = self.client.post("/applications/from-opportunity/999999")
        self.assertEqual(err_opp.status_code, 404)


if __name__ == "__main__":
    unittest.main()
