import unittest
from unittest.mock import patch, MagicMock

from app.core.providers.base import BaseAIProvider
from app.core.providers.ollama import OllamaProvider
from app.core.providers.gemini import GeminiProvider
from app.core.providers.openrouter import OpenRouterProvider
from app.core.brain.manager import (
    process_message,
    get_provider,
    _PROVIDERS,
)
from app.core.planner.registry import TOOLS


class Phase1ValidationTests(unittest.TestCase):

    def test_tool_registry_contract(self):
        """Verify tool registry contains code intelligence and search tools."""
        self.assertIn("code_intelligence", TOOLS)
        self.assertIn("project_search", TOOLS)
        self.assertIn("find_symbol", TOOLS["code_intelligence"])
        self.assertIn("find_text", TOOLS["project_search"])
        self.assertTrue(callable(TOOLS["code_intelligence"]["find_symbol"]))
        self.assertTrue(callable(TOOLS["project_search"]["find_text"]))

    def test_provider_hierarchy(self):
        """Verify provider classes inherit from BaseAIProvider."""
        self.assertTrue(issubclass(OllamaProvider, BaseAIProvider))
        self.assertTrue(issubclass(GeminiProvider, BaseAIProvider))
        self.assertTrue(issubclass(OpenRouterProvider, BaseAIProvider))

    def test_provider_registration(self):
        """Verify provider discovery in brain manager."""
        self.assertIsInstance(_PROVIDERS, dict)
        self.assertIn("ollama", _PROVIDERS)
        self.assertIn("gemini", _PROVIDERS)
        self.assertIn("openrouter", _PROVIDERS)

    @patch.object(OllamaProvider, "generate", return_value="Ollama generated response")
    @patch.object(OllamaProvider, "is_available", return_value=True)
    def test_ollama_dispatch(self, mock_avail, mock_gen):
        """Verify successful dispatch to Ollama."""
        messages = [{"role": "user", "content": "Hello FRIDAY"}]
        resp = process_message(messages, preferred_provider="ollama")
        self.assertEqual(resp, "Ollama generated response")

    @patch.object(OllamaProvider, "is_available", return_value=True)
    @patch.object(OllamaProvider, "generate", side_effect=RuntimeError("Ollama failed"))
    @patch.object(GeminiProvider, "is_available", return_value=True)
    @patch.object(GeminiProvider, "generate", return_value="Gemini fallback response")
    def test_provider_fallback_chain(self, mock_gem_gen, mock_gem_avail, mock_ol_gen, mock_ol_avail):
        """Verify fallback from Ollama to Gemini when primary provider fails."""
        messages = [{"role": "user", "content": "Hello FRIDAY"}]
        resp = process_message(messages, preferred_provider="ollama")
        self.assertEqual(resp, "Gemini fallback response")

    def test_health_endpoint(self):
        """Verify lightweight /health endpoint returns basic health status and UTC timestamp."""
        from fastapi.testclient import TestClient
        from app.main import app

        client = TestClient(app)
        response = client.get("/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data.get("status"), "healthy")
        self.assertIn("timestamp", data)

    def test_detailed_health_endpoint(self):
        """Verify /health/detailed endpoint returns status, timestamp, application name, version, and environment."""
        from fastapi.testclient import TestClient
        from app.main import app
        from app.config import APP_NAME, VERSION, ENV

        client = TestClient(app)
        response = client.get("/health/detailed")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data.get("status"), "healthy")
        self.assertIn("timestamp", data)
        self.assertEqual(data.get("application"), APP_NAME)
        self.assertEqual(data.get("version"), VERSION)
        self.assertEqual(data.get("environment"), ENV)


if __name__ == "__main__":
    unittest.main()
