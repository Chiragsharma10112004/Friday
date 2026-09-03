import uuid
import unittest
from fastapi.testclient import TestClient

from app.main import app
from app.memory.database import SessionLocal
from app.application_pipeline.schemas import CreateApplicationRequest, ApplicationStatus
from app.application_pipeline.service import ApplicationPipelineService
from app.application_feedback.service import default_feedback_service
from app.application_feedback.schemas import (
    OutcomeType,
    FeedbackStage,
    DifficultyRating,
    ExperienceRating,
    FieldIssueType,
    OutcomeFeedbackCreateRequest,
    AssetVersionCreateRequest,
    FieldIssueCreateRequest,
    FeedbackRankRequest,
)


class Phase8ApplicationFeedbackTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        cls.db = SessionLocal()

    @classmethod
    def tearDownClass(cls):
        cls.db.close()

    def test_01_record_application_outcome(self):
        uid = uuid.uuid4().hex[:6]
        app_res = ApplicationPipelineService.create_application(
            request=CreateApplicationRequest(
                company=f"NeuralCorp_{uid}",
                role="Lead AI Engineer",
                source_url=f"https://neuralcorp.io/jobs/lead-ai-{uid}",
                status=ApplicationStatus.APPLIED,
            ),
            db=self.db
        )
        feedback = default_feedback_service.record_outcome(
            db=self.db,
            req=OutcomeFeedbackCreateRequest(
                application_id=app_res.id,
                outcome_type=OutcomeType.OFFER_RECEIVED,
                feedback_stage=FeedbackStage.OFFER_STAGE,
                reasons_cited=["Strong system architecture & AI engineering skills"],
                skills_passed=["Python", "FastAPI", "Distributed Systems"],
                difficulty=DifficultyRating.CHALLENGING,
                experience=ExperienceRating.POSITIVE,
                salary_offered=180000.0,
            )
        )
        self.assertIsNotNone(feedback.id)
        self.assertEqual(feedback.application_id, app_res.id)
        self.assertEqual(feedback.outcome_type, OutcomeType.OFFER_RECEIVED)
        self.assertEqual(feedback.salary_offered, 180000.0)

    def test_02_register_and_retrieve_asset_versions(self):
        uid = uuid.uuid4().hex[:6]
        app_res = ApplicationPipelineService.create_application(
            request=CreateApplicationRequest(
                company=f"ScalabilityTech_{uid}",
                role="Systems Architect",
                source_url=f"https://scalability.tech/jobs/arch-{uid}",
            ),
            db=self.db
        )
        asset_v1 = default_feedback_service.snapshot_asset_version(
            db=self.db,
            req=AssetVersionCreateRequest(
                application_id=app_res.id,
                resume_summary="Senior AI & Distributed Systems Architect",
                customizations_applied=["Distributed Systems", "Kubernetes", "FastAPI"],
                asset_score_at_application=95.0,
            )
        )
        self.assertIsNotNone(asset_v1.id)
        self.assertEqual(len(asset_v1.customizations_applied), 3)

        assets = default_feedback_service.get_asset_versions(
            db=self.db,
            application_id=app_res.id
        )
        self.assertTrue(len(assets) >= 1)
        self.assertEqual(assets[0].application_id, app_res.id)

    def test_03_track_field_issue(self):
        uid = uuid.uuid4().hex[:6]
        app_res = ApplicationPipelineService.create_application(
            request=CreateApplicationRequest(
                company=f"DataFlow_{uid}",
                role="Backend Developer",
                source_url=f"https://dataflow.io/jobs/be-dev-{uid}",
            ),
            db=self.db
        )
        issue = default_feedback_service.log_field_issue(
            db=self.db,
            req=FieldIssueCreateRequest(
                application_id=app_res.id,
                field_name="portfolio_url",
                issue_type=FieldIssueType.VALIDATION_ERROR,
                error_message="URL must start with https://",
            )
        )
        self.assertEqual(issue.field_name, "portfolio_url")
        self.assertEqual(issue.issue_type, FieldIssueType.VALIDATION_ERROR)
        self.assertFalse(issue.resolved)

    def test_04_feedback_analytics_summary(self):
        analytics = default_feedback_service.get_analytics_summary(db=self.db)
        self.assertGreaterEqual(analytics.total_tracked, 1)

    def test_05_feedback_ranking_engine(self):
        rank_res = default_feedback_service.rank_opportunity(
            db=self.db,
            req=FeedbackRankRequest(
                company="NeuralCorp",
                role="Lead AI Engineer",
                match_score=85,
                missing_skills=["Kubernetes"],
            )
        )
        self.assertIsNotNone(rank_res.adjusted_score)
        self.assertIsNotNone(rank_res.priority)

    def test_06_api_endpoints_integration(self):
        # 1. Analytics summary API
        res = self.client.get("/feedback/analytics/summary")
        self.assertEqual(res.status_code, 200)
        self.assertIn("total_tracked", res.json())

        # 2. Conversion funnel API
        funnel_res = self.client.get("/feedback/analytics/funnel")
        self.assertEqual(funnel_res.status_code, 200)
        self.assertIn("discovered", funnel_res.json())

        # 3. Learning signals API
        signals_res = self.client.get("/feedback/signals")
        self.assertEqual(signals_res.status_code, 200)
        self.assertIsInstance(signals_res.json(), list)


if __name__ == "__main__":
    unittest.main()
