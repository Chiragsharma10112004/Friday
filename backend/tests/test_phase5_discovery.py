import unittest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from app.main import app
from app.memory.database import SessionLocal
from app.profile.models import UserProfile
from app.job_discovery.schemas import (
    JobSearchQuery,
    JobSearchResponse,
    ManualDiscoveryRequest,
    ManualDiscoveryResponse,
    PipelineStatus,
)
from app.job_discovery.service import default_discovery_service


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
                skills="Python, FastAPI, Docker, SQL",
            )
            cls.db.add(profile)
            cls.db.commit()
            cls.db.refresh(profile)
        cls.profile = profile

    @classmethod
    def tearDownClass(cls):
        cls.db.close()

    @patch("app.job_discovery.providers.greenhouse.SafeHttpClient.get")
    def test_01_greenhouse_discovery_search(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "jobs": [
                {
                    "id": 1001,
                    "title": "Backend Software Engineer",
                    "location": {"name": "Remote"},
                    "absolute_url": "https://boards.greenhouse.io/testco/jobs/1001",
                    "content": "We are seeking a Python backend engineer with FastAPI experience."
                }
            ]
        }
        mock_get.return_value = mock_resp

        query = JobSearchQuery(
            providers=["greenhouse"],
            companies=["testco"],
            keywords=["Python"]
        )
        res = default_discovery_service.search_and_discover(query, self.db)
        self.assertTrue(res.success)
        self.assertGreater(len(res.opportunities), 0)
        self.assertEqual(res.opportunities[0].provider, "greenhouse")
        self.assertEqual(res.opportunities[0].title, "Backend Software Engineer")

    @patch("app.job_discovery.providers.lever.SafeHttpClient.get")
    def test_02_lever_discovery_search(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = [
            {
                "id": "lever-123",
                "text": "Senior Platform Engineer",
                "categories": {"location": "San Francisco, CA", "commitment": "Full-time"},
                "hostedUrl": "https://jobs.lever.co/testlever/lever-123",
                "descriptionPlain": "Build scalable cloud platforms in Python."
            }
        ]
        mock_get.return_value = mock_resp

        query = JobSearchQuery(
            providers=["lever"],
            companies=["testlever"]
        )
        res = default_discovery_service.search_and_discover(query, self.db)
        self.assertTrue(res.success)
        self.assertEqual(len(res.opportunities), 1)
        self.assertEqual(res.opportunities[0].provider, "lever")

    @patch("app.job_discovery.providers.manual.default_ingestion_service.ingest_job")
    def test_03_manual_discovery_registration(self, mock_ingest):
        from app.ingestion.schemas import NormalizedJobPosting, IngestJobResponse
        mock_ingest.return_value = IngestJobResponse(
            success=True,
            data=NormalizedJobPosting(
                company="DiscoveryCorp",
                role="AI Research Engineer",
                job_description="Research and develop generative AI agents in Python.",
                source_platform="generic",
                source_url="https://discoverycorp.com/careers/ai-eng",
                location="San Francisco, CA",
                confidence="high"
            )
        )
        req = ManualDiscoveryRequest(
            urls=["https://discoverycorp.com/careers/ai-eng"]
        )
        res = default_discovery_service.ingest_manual_urls(req, self.db)
        self.assertTrue(res.success)
        self.assertEqual(res.total_submitted, 1)
        self.assertEqual(len(res.opportunities), 1)
        self.assertEqual(res.opportunities[0].company, "DiscoveryCorp")

    @patch("app.job_discovery.providers.greenhouse.SafeHttpClient.get")
    def test_04_api_search_endpoint(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "jobs": [
                {
                    "id": 2002,
                    "title": "Data Infrastructure Engineer",
                    "location": {"name": "Bengaluru, India"},
                    "absolute_url": "https://boards.greenhouse.io/testinfra/jobs/2002",
                    "content": "Experience with data pipelines and distributed systems."
                }
            ]
        }
        mock_get.return_value = mock_resp

        # 1. POST /job-discovery/search
        search_payload = {
            "providers": ["greenhouse"],
            "companies": ["testinfra"],
            "keywords": ["Data"]
        }
        resp = self.client.post("/job-discovery/search", json=search_payload)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["total_discovered"], 1)


if __name__ == "__main__":
    unittest.main()

