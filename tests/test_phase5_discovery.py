import unittest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
import json

from app.main import app
from app.memory.database import SessionLocal
from app.profile.models import UserProfile
from app.job_discovery.models import DiscoveredOpportunity
from app.job_discovery.schemas import (
    DiscoveredJob,
    JobSearchQuery,
    JobSearchResponse,
    ManualDiscoveryRequest,
    ManualDiscoveryResponse,
    OpportunityFilterParams,
    PipelineStatus,
    JobRecommendation,
    UpdateOpportunityStatusRequest,
)
from app.job_discovery.errors import DiscoveryErrorCode, DiscoveryException
from app.job_discovery.service import default_discovery_service
from app.job_discovery.providers.greenhouse import GreenhouseDiscoveryProvider
from app.job_discovery.providers.lever import LeverDiscoveryProvider
from app.job_discovery.providers.manual import ManualUrlProvider
from app.job_discovery.deduplication import JobDeduplicator
from app.job_discovery.filters import JobFilterEngine
from app.job_discovery.ranking import JobRanker
from app.job_discovery.repository import OpportunityRepository


class Phase5DiscoveryTests(unittest.TestCase):

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

    @classmethod
    def tearDownClass(cls):
        cls.db.close()

    def _get_mock_analysis(self):
        return {
            "match_score": 85,
            "recommendation": "APPLY",
            "strong_matches": ["Python", "FastAPI", "SQLAlchemy"],
            "project_matches": ["FRIDAY Assistant"],
            "partial_matches": ["Docker"],
            "missing_skills": ["Kubernetes"],
            "learnable_skills": ["Kubernetes"],
            "reason": "Strong match on core backend skills with minor gap in K8s.",
            "resume_focus": "FastAPI and LLMs",
            "interview_topics": ["Async IO", "Database scaling"]
        }

    def _get_mock_greenhouse_api_response(self):
        return {
            "jobs": [
                {
                    "id": 1001,
                    "title": "Senior AI Systems Engineer",
                    "location": {"name": "San Francisco, CA (Remote)"},
                    "content": "<p>We are looking for a Senior AI Systems Engineer with Python and FastAPI experience.</p>",
                    "absolute_url": "https://boards.greenhouse.io/anthropic/jobs/1001",
                    "updated_at": "2026-08-20T12:00:00Z"
                },
                {
                    "id": 1002,
                    "title": "Junior Frontend Developer",
                    "location": {"name": "New York, NY"},
                    "content": "<p>Frontend React Developer position.</p>",
                    "absolute_url": "https://boards.greenhouse.io/anthropic/jobs/1002",
                    "updated_at": "2026-08-19T10:00:00Z"
                }
            ]
        }

    def _get_mock_lever_api_response(self):
        return [
            {
                "id": "lever-2001",
                "text": "Senior Backend Infrastructure Engineer",
                "categories": {
                    "location": "Remote",
                    "commitment": "Full-time",
                    "workplaceType": "Remote"
                },
                "descriptionPlain": "Build scalable backend APIs in Python and distributed systems.",
                "hostedUrl": "https://jobs.lever.co/figma/lever-2001",
                "applyUrl": "https://jobs.lever.co/figma/lever-2001/apply",
                "createdAt": 1724000000000
            }
        ]

    # 1. Provider Normalization Tests
    @patch("app.job_discovery.providers.greenhouse.SafeHttpClient.get")
    def test_01_greenhouse_provider_normalization(self, mock_http):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = self._get_mock_greenhouse_api_response()
        mock_http.return_value = mock_resp

        provider = GreenhouseDiscoveryProvider()
        query = JobSearchQuery(companies=["anthropic"])
        jobs = provider.search_jobs(query)

        self.assertEqual(len(jobs), 2)
        job = jobs[0]
        self.assertEqual(job.external_id, "1001")
        self.assertEqual(job.provider, "greenhouse")
        self.assertEqual(job.company, "Anthropic")
        self.assertEqual(job.title, "Senior AI Systems Engineer")
        self.assertTrue(job.is_remote)
        self.assertIn("Python and FastAPI", job.description)

    @patch("app.job_discovery.providers.lever.SafeHttpClient.get")
    def test_02_lever_provider_normalization(self, mock_http):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = self._get_mock_lever_api_response()
        mock_http.return_value = mock_resp

        provider = LeverDiscoveryProvider()
        query = JobSearchQuery(companies=["figma"])
        jobs = provider.search_jobs(query)

        self.assertEqual(len(jobs), 1)
        job = jobs[0]
        self.assertEqual(job.external_id, "lever-2001")
        self.assertEqual(job.provider, "lever")
        self.assertEqual(job.company, "Figma")
        self.assertEqual(job.employment_type, "Full-time")
        self.assertTrue(job.is_remote)

    @patch("app.ingestion.service.default_ingestion_service.ingest_job")
    def test_03_manual_url_provider_delegation_to_phase2(self, mock_ingest):
        from app.ingestion.schemas import IngestJobResponse, NormalizedJobPosting
        mock_ingest.return_value = IngestJobResponse(
            success=True,
            source_platform="greenhouse",
            data=NormalizedJobPosting(
                company="OpenAI",
                role="Research Engineer",
                job_description="Research in LLMs and AI agent architectures.",
                source_platform="greenhouse",
                source_url="https://boards.greenhouse.io/openai/jobs/555",
                location="San Francisco, CA"
            )
        )

        provider = ManualUrlProvider()
        job = provider.fetch_job("https://boards.greenhouse.io/openai/jobs/555")
        self.assertIsNotNone(job)
        self.assertEqual(job.company, "OpenAI")
        self.assertEqual(job.title, "Research Engineer")
        self.assertEqual(job.provider, "greenhouse")

    def test_04_unsupported_provider_rejection(self):
        query = JobSearchQuery(providers=["unsupported_ats_name"])
        with self.assertRaises(DiscoveryException) as ctx:
            default_discovery_service.search_and_discover(query, self.db)
        self.assertEqual(ctx.exception.code, DiscoveryErrorCode.PROVIDER_UNSUPPORTED)

    # 2. Search & Filtering Tests
    def test_05_search_filtering(self):
        job1 = DiscoveredJob(
            provider="greenhouse",
            source_url="https://boards.greenhouse.io/a/1",
            company="Alpha",
            title="Senior Python Backend Engineer",
            location="Remote",
            is_remote=True,
            description="Python FastAPI backend role."
        )
        job2 = DiscoveredJob(
            provider="greenhouse",
            source_url="https://boards.greenhouse.io/a/2",
            company="Beta",
            title="iOS Swift Developer",
            location="Austin, TX",
            is_remote=False,
            description="Mobile iOS Swift app development."
        )

        query = JobSearchQuery(roles=["Python", "Backend"], remote_only=True)
        filtered = JobFilterEngine.filter_jobs([job1, job2], query)
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0].title, "Senior Python Backend Engineer")

    def test_06_empty_result_handling(self):
        query = JobSearchQuery(roles=["Astronaut Developer"])
        job = DiscoveredJob(
            provider="greenhouse",
            source_url="https://boards.greenhouse.io/a/1",
            company="Alpha",
            title="Python Engineer",
            description="Backend role"
        )
        filtered = JobFilterEngine.filter_jobs([job], query)
        self.assertEqual(len(filtered), 0)

    # 3. Deduplication Tests
    def test_07_exact_id_deduplication(self):
        job1 = DiscoveredJob(external_id="101", provider="greenhouse", source_url="https://gh.io/1", company="A", title="Dev", description="Desc 1")
        job2 = DiscoveredJob(external_id="101", provider="greenhouse", source_url="https://gh.io/1-duplicate", company="A", title="Dev", description="Desc 2")
        unique, skipped = JobDeduplicator.deduplicate([job1, job2])
        self.assertEqual(len(unique), 1)
        self.assertEqual(skipped, 1)

    def test_08_canonical_url_deduplication(self):
        job1 = DiscoveredJob(provider="generic", source_url="https://careers.company.com/job/10?utm_source=linkedin&ref=board", company="A", title="Dev", description="Desc")
        job2 = DiscoveredJob(provider="generic", source_url="https://careers.company.com/job/10", company="A", title="Dev", description="Desc")
        unique, skipped = JobDeduplicator.deduplicate([job1, job2])
        self.assertEqual(len(unique), 1)
        self.assertEqual(skipped, 1)

    def test_09_entity_matching_deduplication(self):
        job1 = DiscoveredJob(provider="greenhouse", source_url="https://boards.greenhouse.io/corp/1", company="Stripe", title="Senior Software Engineer - Payments", location="San Francisco, CA", description="Payments backend")
        job2 = DiscoveredJob(provider="lever", source_url="https://jobs.lever.co/stripe/2", company="Stripe", title="Senior Software Engineer Payments", location="San Francisco CA", description="Payments backend")
        unique, skipped = JobDeduplicator.deduplicate([job1, job2])
        self.assertEqual(len(unique), 1)
        self.assertEqual(skipped, 1)

    # 4. Candidate Matching & Ranking Tests
    @patch("app.job_discovery.ranking.analyze_job")
    def test_10_candidate_match_ranking(self, mock_analyze):
        mock_analyze.return_value = self._get_mock_analysis()

        job = DiscoveredJob(
            provider="manual",
            source_url="https://example.com/job/fastapi",
            company="FastTech",
            title="Senior Python FastAPI Developer",
            description="Requires strong demonstrated skills in Python, FastAPI, SQLAlchemy, and PostgreSQL."
        )

        ranked_job = JobRanker.evaluate_match(job, self.db, self.profile)
        self.assertIsNotNone(ranked_job.match_score)
        self.assertEqual(ranked_job.match_score, 85)
        self.assertEqual(ranked_job.recommendation, JobRecommendation.STRONG_MATCH)
        self.assertGreater(len(ranked_job.matched_skills), 0)
        self.assertIn("Python", ranked_job.matched_skills)

    # 5. Opportunity Pipeline Lifecycle Tests
    def test_11_opportunity_creation_and_status_transitions(self):
        job = DiscoveredJob(
            external_id="disc-999",
            provider="greenhouse",
            source_url="https://boards.greenhouse.io/acme/jobs/999",
            company="Acme Corp",
            title="Platform Engineer",
            description="Build cloud platforms in Python.",
            match_score=85,
            recommendation=JobRecommendation.STRONG_MATCH,
            status=PipelineStatus.DISCOVERED
        )

        opp_record = OpportunityRepository.save_opportunity(self.db, job)
        self.assertIsNotNone(opp_record.id)
        opp_id = opp_record.id

        updated = OpportunityRepository.update_opportunity_status(self.db, opp_id, PipelineStatus.SAVED)
        self.assertEqual(updated.status, PipelineStatus.SAVED.value)

        updated2 = OpportunityRepository.update_opportunity_status(self.db, opp_id, PipelineStatus.ANALYZED)
        self.assertEqual(updated2.status, PipelineStatus.ANALYZED.value)

        with self.assertRaises(DiscoveryException) as ctx:
            OpportunityRepository.update_opportunity_status(self.db, opp_id, PipelineStatus.DISCOVERED)
        self.assertEqual(ctx.exception.code, DiscoveryErrorCode.INVALID_STATUS_TRANSITION)

    # 6. HTTP API Integration Tests
    @patch("app.job_discovery.ranking.analyze_job")
    @patch("app.job_discovery.providers.greenhouse.SafeHttpClient.get")
    def test_12_post_job_discovery_search_endpoint(self, mock_http, mock_analyze):
        mock_analyze.return_value = self._get_mock_analysis()
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = self._get_mock_greenhouse_api_response()
        mock_http.return_value = mock_resp

        payload = {
            "companies": ["anthropic"],
            "roles": ["Senior AI"],
            "providers": ["greenhouse"]
        }
        resp = self.client.post("/job-discovery/search", json=payload)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data["success"])
        self.assertGreater(len(data["opportunities"]), 0)
        self.assertEqual(data["opportunities"][0]["company"], "Anthropic")

    @patch("app.job_discovery.ranking.analyze_job")
    @patch("app.ingestion.service.default_ingestion_service.ingest_job")
    def test_13_post_job_discovery_manual_endpoint(self, mock_ingest, mock_analyze):
        mock_analyze.return_value = self._get_mock_analysis()
        from app.ingestion.schemas import IngestJobResponse, NormalizedJobPosting
        mock_ingest.return_value = IngestJobResponse(
            success=True,
            source_platform="lever",
            data=NormalizedJobPosting(
                company="Figma",
                role="Staff Infrastructure Engineer",
                job_description="Distributed infrastructure with Python and cloud containers.",
                source_platform="lever",
                source_url="https://jobs.lever.co/figma/staff-infra",
                location="Remote"
            )
        )

        payload = {"urls": ["https://jobs.lever.co/figma/staff-infra"]}
        resp = self.client.post("/job-discovery/manual", json=payload)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["unique_opportunities"], 1)

    def test_14_get_opportunities_list_and_patch_status_endpoints(self):
        job = DiscoveredJob(
            provider="manual",
            source_url="https://careers.example.com/job/api-test-1",
            company="ApiTestCo",
            title="Backend Lead",
            description="Python and FastAPI lead engineer.",
            match_score=90,
            status=PipelineStatus.DISCOVERED
        )
        saved = OpportunityRepository.save_opportunity(self.db, job)

        list_resp = self.client.get(f"/opportunities?company=ApiTestCo")
        self.assertEqual(list_resp.status_code, 200)
        list_data = list_resp.json()
        self.assertGreater(list_data["total"], 0)

        get_resp = self.client.get(f"/opportunities/{saved.id}")
        self.assertEqual(get_resp.status_code, 200)
        self.assertEqual(get_resp.json()["company"], "ApiTestCo")

        patch_resp = self.client.patch(f"/opportunities/{saved.id}/status", json={"status": "SAVED"})
        self.assertEqual(patch_resp.status_code, 200)
        self.assertEqual(patch_resp.json()["status"], "SAVED")

    # 7. Subsystem Integration Tests (Phases 1, 3, 4)
    @patch("app.job_discovery.service.analyze_job")
    @patch("app.application_assets.service.analyze_job")
    @patch("app.application_assets.service.process_message")
    def test_15_opportunity_analyze_and_assets_integration(self, mock_ai, mock_analyze_assets, mock_analyze_job):
        mock_analyze_job.return_value = self._get_mock_analysis()
        mock_analyze_assets.return_value = self._get_mock_analysis()
        mock_ai.return_value = json.dumps({
            "resume": {
                "professional_summary": "Tailored AI Backend summary.",
                "relevant_skills": ["Python", "FastAPI"],
                "relevant_projects": [],
                "experience_bullets": [],
                "achievement_bullets": [],
                "keywords_matched": ["Python"],
                "keywords_missing": [],
                "sections_to_prioritize": []
            }
        })

        job = DiscoveredJob(
            provider="greenhouse",
            source_url="https://boards.greenhouse.io/integ/101",
            company="IntegCorp",
            title="Senior AI Engineer",
            description="Developing LLM pipelines and backend microservices with FastAPI and Python.",
            status=PipelineStatus.SAVED
        )
        saved = OpportunityRepository.save_opportunity(self.db, job)

        analyze_resp = self.client.post(f"/opportunities/{saved.id}/analyze")
        self.assertEqual(analyze_resp.status_code, 200)
        an_data = analyze_resp.json()
        self.assertEqual(an_data["company"], "IntegCorp")
        self.assertIn("match_score", an_data["analysis"])

        asset_resp = self.client.post(f"/opportunities/{saved.id}/generate-assets")
        self.assertEqual(asset_resp.status_code, 200)
        as_data = asset_resp.json()
        self.assertTrue(as_data["success"])
        self.assertIsNotNone(as_data["assets"]["resume"])

    @patch("app.application_automation.browser.SafeHttpClient.get")
    def test_16_opportunity_prepare_application_phase4_integration(self, mock_http):
        sample_html = """
        <html><body>
            <form id="application_form">
                <input id="first_name" name="first_name" />
                <input id="email" name="email" type="email" />
            </form>
        </body></html>
        """
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = sample_html
        mock_http.return_value = mock_resp

        job = DiscoveredJob(
            provider="greenhouse",
            source_url="https://boards.greenhouse.io/prep/202",
            application_url="https://boards.greenhouse.io/prep/202",
            company="PrepCorp",
            title="Staff Platform Engineer",
            description="Cloud infrastructure and Python backend services.",
            status=PipelineStatus.ASSETS_GENERATED
        )
        saved = OpportunityRepository.save_opportunity(self.db, job)

        prep_resp = self.client.post(f"/opportunities/{saved.id}/prepare-application")
        self.assertEqual(prep_resp.status_code, 200)
        prep_data = prep_resp.json()
        self.assertTrue(prep_data["success"])
        self.assertFalse(prep_data["submission_allowed"])


if __name__ == "__main__":
    unittest.main()

