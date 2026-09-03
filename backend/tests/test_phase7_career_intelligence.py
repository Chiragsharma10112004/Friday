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
)
from app.career_intelligence.models import CareerRecommendation
from app.career_intelligence.schemas import (
    RecommendationType,
    RecommendationStatus,
    ActionPriority,
    HealthCategory,
)
from app.career_intelligence.errors import (
    CareerIntelligenceErrorCode,
    CareerIntelligenceException,
)
from app.career_intelligence.priority_engine import ApplicationPriorityEngine
from app.career_intelligence.health_engine import ApplicationHealthEngine
from app.career_intelligence.recommendation_engine import RecommendationEngine
from app.career_intelligence.service import default_career_intelligence_service


class Phase7CareerIntelligenceTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        cls.db = SessionLocal()

        # Clean Phase 6 and Phase 7 test tables for clean isolated test runs
        cls.db.query(CareerRecommendation).delete()
        cls.db.query(ApplicationStatusHistory).delete()
        cls.db.query(ApplicationInterview).delete()
        cls.db.query(ApplicationTimelineEvent).delete()
        cls.db.query(TrackedApplication).delete()
        cls.db.query(DiscoveredOpportunity).delete()
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

    @classmethod
    def tearDownClass(cls):
        cls.db.close()

    def setUp(self):
        self.db.rollback()

    # =========================================================
    # 1. Priority Scoring Engine
    # =========================================================

    def test_01_priority_score_match_score_and_priority_weighting(self):
        now = datetime.now(timezone.utc)
        app1 = TrackedApplication(
            company="Google",
            role="Staff AI Infrastructure Engineer",
            match_score=95,  # +30
            priority=ApplicationPriority.URGENT.value,  # +25
            referral_status=ReferralStatus.REFERRED.value,  # +15
            status=ApplicationStatus.READY_TO_APPLY.value,  # +20
            follow_up_status=FollowUpStatus.DUE.value,  # +20
        )
        res = ApplicationPriorityEngine.calculate_priority_score(app1, now=now)
        # Sum = 30 + 25 + 15 + 20 + 20 = 110, capped at 100
        self.assertEqual(res.total_score, 100)
        self.assertEqual(res.breakdown["match_score"], 30)
        self.assertEqual(res.breakdown["application_priority"], 25)
        self.assertEqual(res.breakdown["referral"], 15)
        self.assertEqual(res.breakdown["application_state"], 20)
        self.assertEqual(res.breakdown["follow_up"], 20)

    def test_02_priority_score_interview_and_staleness_weighting(self):
        now = datetime.now(timezone.utc)
        tomorrow = now + timedelta(hours=18)
        month_ago = now - timedelta(days=32)

        app2 = TrackedApplication(
            company="Anthropic",
            role="Research Systems Engineer",
            match_score=75,  # +20
            priority=ApplicationPriority.MEDIUM.value,  # +10
            referral_status=ReferralStatus.NOT_REQUESTED.value,  # +0
            status=ApplicationStatus.INTERVIEWING.value,
            interview_date=tomorrow,  # +30 (<24h)
            last_status_update=month_ago,  # +20 (30+ days)
        )
        res = ApplicationPriorityEngine.calculate_priority_score(app2, now=now)
        # Sum = 20 + 10 + 0 + 0 + 0 + 30 + 20 = 80
        self.assertEqual(res.total_score, 80)
        self.assertEqual(res.breakdown["interview"], 30)
        self.assertEqual(res.breakdown["staleness"], 20)

    # =========================================================
    # 2. Application Health Engine
    # =========================================================

    def test_03_application_health_critical_on_overdue(self):
        now = datetime.now(timezone.utc)
        app_crit = TrackedApplication(
            company="OpenAI",
            role="Kernel Engineer",
            status=ApplicationStatus.APPLIED.value,
            follow_up_status=FollowUpStatus.OVERDUE.value,
        )
        health_res = ApplicationHealthEngine.evaluate_health(app_crit, now=now)
        self.assertEqual(health_res.health, HealthCategory.CRITICAL)
        self.assertLessEqual(health_res.score, 30)
        self.assertIn("Follow-up is overdue", health_res.reasons)

    def test_04_application_health_stale_on_inactive_applied(self):
        now = datetime.now(timezone.utc)
        three_weeks_ago = now - timedelta(days=22)
        app_stale = TrackedApplication(
            company="Meta",
            role="Backend Engineer",
            status=ApplicationStatus.APPLIED.value,
            last_status_update=three_weeks_ago,
            follow_up_status=FollowUpStatus.NONE.value,
        )
        health_res = ApplicationHealthEngine.evaluate_health(app_stale, now=now)
        self.assertEqual(health_res.health, HealthCategory.STALE)
        self.assertIn("Application has been inactive", health_res.reasons[0])

    def test_05_application_health_attention_needed_and_excellent(self):
        now = datetime.now(timezone.utc)
        # Attention needed: follow-up DUE today
        app_att = TrackedApplication(
            company="Apple",
            role="ML Frameworks Engineer",
            status=ApplicationStatus.APPLIED.value,
            follow_up_status=FollowUpStatus.DUE.value,
        )
        res_att = ApplicationHealthEngine.evaluate_health(app_att, now=now)
        self.assertEqual(res_att.health, HealthCategory.ATTENTION_NEEDED)

        # Excellent: Offer received
        app_exc = TrackedApplication(
            company="NVIDIA",
            role="CUDA Architecture Lead",
            status=ApplicationStatus.OFFER.value,
        )
        res_exc = ApplicationHealthEngine.evaluate_health(app_exc, now=now)
        self.assertEqual(res_exc.health, HealthCategory.EXCELLENT)
        self.assertGreaterEqual(res_exc.score, 90)

    # =========================================================
    # 3. Recommendation Generation Rules & Deduplication
    # =========================================================

    def test_06_recommendation_generation_and_deduplication(self):
        now = datetime.now(timezone.utc)

        # 1. Create a tracked application requiring follow-up
        yesterday = now - timedelta(days=1)
        app_rec1 = TrackedApplication(
            company="Scale AI",
            role="Data Engine Architect",
            status=ApplicationStatus.APPLIED.value,
            next_follow_up_date=yesterday,
            follow_up_status=FollowUpStatus.OVERDUE.value,
            match_score=85,
        )
        self.db.add(app_rec1)

        # 2. Create an application ready to apply
        app_rec2 = TrackedApplication(
            company="Databricks",
            role="Lakehouse Backend Lead",
            status=ApplicationStatus.READY_TO_APPLY.value,
            match_score=92,
        )
        self.db.add(app_rec2)

        # 3. Create a high-match Phase 5 opportunity
        opp1 = DiscoveredOpportunity(
            external_id="ci-test-opp-1",
            provider="greenhouse",
            source_url="https://boards.greenhouse.io/figma/jobs/901",
            company="Figma",
            title="Design Systems Backend Engineer",
            description="Build scalable distributed services.",
            match_score=88,
            recommendation="STRONG_MATCH",
            status="DISCOVERED"
        )
        self.db.add(opp1)
        self.db.commit()

        # Run Refresh
        refresh_res = default_career_intelligence_service.refresh_recommendations(self.db, now=now)
        self.assertTrue(refresh_res.success)
        self.assertGreaterEqual(refresh_res.active_count, 3)

        # Verify specific recommendations exist
        recs = default_career_intelligence_service.get_next_actions(self.db)
        types = [r.type for r in recs]
        self.assertIn(RecommendationType.FOLLOW_UP_OVERDUE, types)
        self.assertIn(RecommendationType.APPLY_NOW, types)
        self.assertIn(RecommendationType.PRIORITY_APPLICATION, types)

        # Idempotent re-refresh: does NOT duplicate active recommendations
        refresh_res2 = default_career_intelligence_service.refresh_recommendations(self.db, now=now)
        self.assertEqual(refresh_res2.created_count, 0)
        self.assertEqual(refresh_res2.active_count, refresh_res.active_count)

    def test_07_recommendation_expiration_when_condition_cleared(self):
        now = datetime.now(timezone.utc)

        # Create application with due follow-up
        app_exp = TrackedApplication(
            company="Snowflake",
            role="Core Engine Developer",
            status=ApplicationStatus.APPLIED.value,
            next_follow_up_date=now,
            follow_up_status=FollowUpStatus.DUE.value,
        )
        self.db.add(app_exp)
        self.db.commit()

        # Refresh creates FOLLOW_UP_DUE recommendation
        default_career_intelligence_service.refresh_recommendations(self.db, now=now)
        rec_due = self.db.query(CareerRecommendation).filter(
            CareerRecommendation.application_id == app_exp.id,
            CareerRecommendation.recommendation_type == RecommendationType.FOLLOW_UP_DUE.value,
            CareerRecommendation.status == RecommendationStatus.ACTIVE.value
        ).first()
        self.assertIsNotNone(rec_due)

        # Clear condition: mark follow-up completed
        app_exp.follow_up_status = FollowUpStatus.COMPLETED.value
        self.db.commit()

        # Next refresh expires the recommendation
        default_career_intelligence_service.refresh_recommendations(self.db, now=now)
        self.db.refresh(rec_due)
        self.assertEqual(rec_due.status, RecommendationStatus.EXPIRED.value)

    def test_08_dismiss_and_complete_recommendations(self):
        now = datetime.now(timezone.utc)
        app_user = TrackedApplication(
            company="Vercel",
            role="Edge Runtime Engineer",
            status=ApplicationStatus.SAVED.value,
            match_score=78,
            date_assets_generated=None,
        )
        self.db.add(app_user)
        self.db.commit()

        default_career_intelligence_service.refresh_recommendations(self.db, now=now)
        rec = self.db.query(CareerRecommendation).filter(
            CareerRecommendation.application_id == app_user.id,
            CareerRecommendation.status == RecommendationStatus.ACTIVE.value
        ).first()
        self.assertIsNotNone(rec)

        # Dismiss
        dismissed = default_career_intelligence_service.dismiss_recommendation(rec.id, self.db)
        self.assertEqual(dismissed.status, RecommendationStatus.DISMISSED)

        # Cannot dismiss non-active
        with self.assertRaises(CareerIntelligenceException) as ctx:
            default_career_intelligence_service.dismiss_recommendation(rec.id, self.db)
        self.assertEqual(ctx.exception.code, CareerIntelligenceErrorCode.INVALID_RECOMMENDATION_STATE)

    # =========================================================
    # 4. Today Queue, Health, Briefings & Dashboard REST API
    # =========================================================

    def test_09_api_today_action_queue(self):
        res = self.client.get("/career-intelligence/today")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data["success"])
        self.assertIn("actions", data)
        self.assertIn("summary", data)
        self.assertIn("urgent_count", data)

    def test_10_api_application_health_endpoints(self):
        # 1. All applications health
        res_all = self.client.get("/career-intelligence/application-health")
        self.assertEqual(res_all.status_code, 200)
        data_all = res_all.json()
        self.assertIn("items", data_all)
        self.assertGreater(data_all["total"], 0)

        first_app_id = data_all["items"][0]["application_id"]

        # 2. Single application health
        res_single = self.client.get(f"/career-intelligence/application-health/{first_app_id}")
        self.assertEqual(res_single.status_code, 200)
        data_single = res_single.json()
        self.assertEqual(data_single["application_id"], first_app_id)
        self.assertIn("health", data_single)
        self.assertIn("health_score", data_single)

        # 3. Not found health (404)
        res_404 = self.client.get("/career-intelligence/application-health/999999")
        self.assertEqual(res_404.status_code, 404)

    def test_11_api_dashboard_and_briefings(self):
        # 1. Dashboard
        dash_res = self.client.get("/career-intelligence/dashboard")
        self.assertEqual(dash_res.status_code, 200)
        dash_data = dash_res.json()
        self.assertIn("total_active_applications", dash_data)
        self.assertIn("average_application_health", dash_data)
        self.assertIn("top_priority_applications", dash_data)

        # 2. Daily briefing
        daily_res = self.client.get("/career-intelligence/daily-briefing")
        self.assertEqual(daily_res.status_code, 200)
        daily_data = daily_res.json()
        self.assertIn("summary", daily_data)
        self.assertIn("top_opportunities", daily_data)

        # 3. Weekly briefing
        weekly_res = self.client.get("/career-intelligence/weekly-briefing")
        self.assertEqual(weekly_res.status_code, 200)
        weekly_data = weekly_res.json()
        self.assertIn("total_applications", weekly_data)
        self.assertIn("recommended_focus_next_week", weekly_data)

    def test_12_api_recommendation_actions(self):
        # Get active recommendation
        actions_res = self.client.get("/career-intelligence/next-actions")
        self.assertEqual(actions_res.status_code, 200)
        actions = actions_res.json()

        if actions:
            target_id = actions[0]["id"]
            # Complete recommendation
            comp_res = self.client.post(f"/career-intelligence/recommendations/{target_id}/complete")
            self.assertEqual(comp_res.status_code, 200)
            self.assertEqual(comp_res.json()["status"], "COMPLETED")

        # Non-existent recommendation (404)
        err_res = self.client.post("/career-intelligence/recommendations/999999/dismiss")
        self.assertEqual(err_res.status_code, 404)

    def test_13_closed_applications_excluded_from_intelligence(self):
        now = datetime.now(timezone.utc)
        closed_app = TrackedApplication(
            company="Enron",
            role="Legacy Accounting",
            status=ApplicationStatus.CLOSED.value,
            follow_up_status=FollowUpStatus.OVERDUE.value,  # would be critical if active
        )
        self.db.add(closed_app)
        self.db.commit()

        candidates = RecommendationEngine.evaluate_candidates(self.db, now=now)
        app_ids_in_candidates = {c.application_id for c in candidates}
        self.assertNotIn(closed_app.id, app_ids_in_candidates)


if __name__ == "__main__":
    unittest.main()

