import unittest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from app.main import app
from app.ingestion.schemas import IngestJobRequest, IngestJobResponse
from app.ingestion.errors import IngestionErrorCode, IngestionException
from app.ingestion.validators import (
    validate_url_syntax,
    validate_hostname_against_ssrf,
    SafeHttpClient,
)
from app.ingestion.detector import PlatformDetector
from app.ingestion.extractors.greenhouse import GreenhouseExtractor
from app.ingestion.extractors.lever import LeverExtractor
from app.ingestion.extractors.generic import GenericExtractor
from app.ingestion.service import default_ingestion_service


class Phase2IngestionTests(unittest.TestCase):

    def setUp(self):
        self.client = TestClient(app)

    # ==========================================
    # 1. URL Syntax & Validation Tests
    # ==========================================

    def test_url_syntax_valid(self):
        parsed = validate_url_syntax("https://boards.greenhouse.io/openai/jobs/123")
        self.assertEqual(parsed.scheme, "https")
        self.assertEqual(parsed.netloc, "boards.greenhouse.io")

    def test_url_syntax_invalid_scheme(self):
        with self.assertRaises(IngestionException) as ctx:
            validate_url_syntax("ftp://boards.greenhouse.io/job/123")
        self.assertEqual(ctx.exception.code, IngestionErrorCode.INVALID_URL)

    def test_url_syntax_file_scheme(self):
        with self.assertRaises(IngestionException) as ctx:
            validate_url_syntax("file:///etc/passwd")
        self.assertEqual(ctx.exception.code, IngestionErrorCode.INVALID_URL)

    # ==========================================
    # 2. SSRF Protection Tests
    # ==========================================

    @patch("socket.getaddrinfo")
    def test_ssrf_blocks_localhost(self, mock_dns):
        mock_dns.return_value = [(2, 1, 6, "", ("127.0.0.1", 80))]
        with self.assertRaises(IngestionException) as ctx:
            validate_hostname_against_ssrf("localhost")
        self.assertEqual(ctx.exception.code, IngestionErrorCode.SSRF_ATTEMPT_BLOCKED)

    @patch("socket.getaddrinfo")
    def test_ssrf_blocks_private_ip(self, mock_dns):
        mock_dns.return_value = [(2, 1, 6, "", ("192.168.1.50", 80))]
        with self.assertRaises(IngestionException) as ctx:
            validate_hostname_against_ssrf("internal.corp")
        self.assertEqual(ctx.exception.code, IngestionErrorCode.SSRF_ATTEMPT_BLOCKED)

    @patch("socket.getaddrinfo")
    def test_ssrf_blocks_aws_metadata(self, mock_dns):
        mock_dns.return_value = [(2, 1, 6, "", ("169.254.169.254", 80))]
        with self.assertRaises(IngestionException) as ctx:
            validate_hostname_against_ssrf("metadata.internal")
        self.assertEqual(ctx.exception.code, IngestionErrorCode.SSRF_ATTEMPT_BLOCKED)

    # ==========================================
    # 3. Platform Detection Tests
    # ==========================================

    def test_detect_greenhouse(self):
        parsed = validate_url_syntax("https://boards.greenhouse.io/stripe/jobs/12345")
        platform = PlatformDetector.detect(parsed.geturl(), parsed)
        self.assertEqual(platform, "greenhouse")

    def test_detect_lever(self):
        parsed = validate_url_syntax("https://jobs.lever.co/figma/abc-123")
        platform = PlatformDetector.detect(parsed.geturl(), parsed)
        self.assertEqual(platform, "lever")

    def test_detect_linkedin(self):
        parsed = validate_url_syntax("https://www.linkedin.com/jobs/view/123456")
        platform = PlatformDetector.detect(parsed.geturl(), parsed)
        self.assertEqual(platform, "linkedin")

    def test_detect_indeed(self):
        parsed = validate_url_syntax("https://indeed.com/viewjob?jk=12345")
        platform = PlatformDetector.detect(parsed.geturl(), parsed)
        self.assertEqual(platform, "indeed")

    def test_detect_generic(self):
        parsed = validate_url_syntax("https://careers.google.com/jobs/results/123")
        platform = PlatformDetector.detect(parsed.geturl(), parsed)
        self.assertEqual(platform, "generic")

    # ==========================================
    # 4. Extractor Tests (Mocked Offline)
    # ==========================================

    @patch("app.ingestion.extractors.greenhouse.SafeHttpClient.get")
    def test_greenhouse_api_extraction(self, mock_http):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "id": 12345,
            "title": "Software Engineer, Core Backend",
            "content": "<p>We are seeking a <strong>Python</strong> engineer.</p><ul><li>Build APIs</li></ul>",
            "departments": [{"name": "Engineering"}],
            "location": {"name": "Remote, US"},
            "updated_at": "2026-03-01T00:00:00Z"
        }
        mock_http.return_value = mock_resp

        parsed = validate_url_syntax("https://boards.greenhouse.io/stripe/jobs/12345")
        extractor = GreenhouseExtractor()
        posting = extractor.extract(parsed.geturl(), parsed)

        self.assertEqual(posting.company, "Stripe")
        self.assertEqual(posting.role, "Software Engineer, Core Backend")
        self.assertIn("Python", posting.job_description)
        self.assertIn("Build APIs", posting.job_description)
        self.assertEqual(posting.location, "Remote, US")
        self.assertEqual(posting.source_platform, "greenhouse")

    @patch("app.ingestion.extractors.lever.SafeHttpClient.get")
    def test_lever_api_extraction(self, mock_http):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "id": "lever-123",
            "text": "Full Stack Engineer",
            "descriptionPlain": "We are looking for a Full Stack Engineer to join our team.",
            "categories": {
                "location": "San Francisco, CA",
                "team": "Product Engineering",
                "commitment": "Full-time",
                "workplaceType": "Hybrid"
            },
            "lists": [
                {
                    "text": "Requirements",
                    "content": "<li>FastAPI and React</li><li>SQLAlchemy</li>"
                }
            ]
        }
        mock_http.return_value = mock_resp

        parsed = validate_url_syntax("https://jobs.lever.co/figma/lever-123")
        extractor = LeverExtractor()
        posting = extractor.extract(parsed.geturl(), parsed)

        self.assertEqual(posting.company, "Figma")
        self.assertEqual(posting.role, "Full Stack Engineer")
        self.assertIn("FastAPI and React", posting.job_description)
        self.assertEqual(posting.location, "San Francisco, CA")
        self.assertEqual(posting.source_platform, "lever")

    @patch("app.ingestion.extractors.generic.SafeHttpClient.get")
    def test_generic_json_ld_extraction(self, mock_http):
        html_doc = """
        <html>
        <head>
            <script type="application/ld+json">
            {
                "@context": "https://schema.org",
                "@type": "JobPosting",
                "title": "Principal AI Architect",
                "description": "<p>Design and deploy LLM applications with FastAPI and PyTorch.</p>",
                "hiringOrganization": {
                    "@type": "Organization",
                    "name": "NeuralTech Corp"
                },
                "jobLocation": {
                    "address": "New York, NY"
                },
                "employmentType": "FULL_TIME"
            }
            </script>
        </head>
        <body><h1>Careers</h1></body>
        </html>
        """
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = html_doc
        mock_http.return_value = mock_resp

        parsed = validate_url_syntax("https://neuraltech.io/careers/principal-architect")
        extractor = GenericExtractor()
        posting = extractor.extract(parsed.geturl(), parsed)

        self.assertEqual(posting.company, "NeuralTech Corp")
        self.assertEqual(posting.role, "Principal AI Architect")
        self.assertIn("FastAPI and PyTorch", posting.job_description)
        self.assertEqual(posting.location, "New York, NY")

    # ==========================================
    # 5. Access Restricted Source Handling
    # ==========================================

    def test_linkedin_access_restricted_policy(self):
        req = IngestJobRequest(job_url="https://www.linkedin.com/jobs/view/987654321")
        resp: IngestJobResponse = default_ingestion_service.ingest_job(req)

        self.assertFalse(resp.success)
        self.assertEqual(resp.source_platform, "linkedin")
        self.assertEqual(len(resp.errors), 1)
        self.assertEqual(resp.errors[0].code, IngestionErrorCode.SOURCE_ACCESS_RESTRICTED)

    def test_indeed_access_restricted_policy(self):
        req = IngestJobRequest(job_url="https://indeed.com/viewjob?jk=abcdef123456")
        resp: IngestJobResponse = default_ingestion_service.ingest_job(req)

        self.assertFalse(resp.success)
        self.assertEqual(resp.source_platform, "indeed")
        self.assertEqual(len(resp.errors), 1)
        self.assertEqual(resp.errors[0].code, IngestionErrorCode.SOURCE_ACCESS_RESTRICTED)

    # ==========================================
    # 6. HTTP API Endpoint Integration
    # ==========================================

    @patch("app.ingestion.extractors.greenhouse.SafeHttpClient.get")
    def test_post_jobs_ingest_endpoint(self, mock_http):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "id": 999,
            "title": "Senior AI Engineer",
            "content": "<p>Work on state of the art LLM platforms.</p>",
            "location": {"name": "Remote"}
        }
        mock_http.return_value = mock_resp

        payload = {"job_url": "https://boards.greenhouse.io/anthropic/jobs/999"}
        response = self.client.post("/jobs/ingest", json=payload)

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data.get("success"))
        self.assertEqual(data.get("source_platform"), "greenhouse")
        self.assertEqual(data.get("data", {}).get("company"), "Anthropic")


if __name__ == "__main__":
    unittest.main()

