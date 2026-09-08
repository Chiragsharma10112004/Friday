"""
Unit tests for production provider routing, intelligent fallbacks, and CORS headers.
"""
import unittest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from app.main import app
from app.core.brain.manager import resolve_best_provider_name, get_provider, process_message
from app.core.providers.ollama import OllamaProvider
from app.core.providers.gemini import GeminiProvider
from app.core.providers.openrouter import OpenRouterProvider


class ProductionProviderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_01_openrouter_selected_when_key_present(self):
        with patch("app.config.OPENROUTER_API_KEY", "sk-or-v1-testkey12345"):
            with patch("app.config.ENV", "production"):
                name = resolve_best_provider_name()
                self.assertEqual(name, "openrouter")
                prov = get_provider()
                self.assertIsInstance(prov, OpenRouterProvider)
                self.assertTrue(prov.is_available())

    def test_02_gemini_selected_when_only_gemini_key_present(self):
        with patch("app.config.OPENROUTER_API_KEY", ""):
            with patch("app.config.GEMINI_API_KEY", "AIzaSyTestKey12345"):
                with patch("app.config.ENV", "production"):
                    name = resolve_best_provider_name()
                    self.assertEqual(name, "gemini")
                    prov = get_provider()
                    self.assertIsInstance(prov, GeminiProvider)
                    self.assertTrue(prov.is_available())

    def test_03_production_mode_ollama_not_available(self):
        with patch("app.config.ENV", "production"):
            ollama = OllamaProvider()
            self.assertFalse(ollama.is_available())

    def test_04_fallback_from_failed_primary_to_secondary(self):
        with patch("app.config.OPENROUTER_API_KEY", "sk-test-key"):
            with patch("app.config.GEMINI_API_KEY", "gem-test-key"):
                # OpenRouter primary throws an error
                with patch.object(OpenRouterProvider, "generate", side_effect=RuntimeError("Rate limited")):
                    # Gemini fallback succeeds
                    with patch.object(GeminiProvider, "generate", return_value="Response from Gemini fallback"):
                        result = process_message(
                            messages=[{"role": "user", "content": "Hello FRIDAY"}],
                            preferred_provider="openrouter"
                        )
                        self.assertEqual(result, "Response from Gemini fallback")

    def test_05_cors_allows_vercel_production_origin(self):
        response = self.client.options(
            "/status",
            headers={
                "Origin": "https://friday-ai-eosin.vercel.app",
                "Access-Control-Request-Method": "GET",
            }
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.headers.get("access-control-allow-origin"),
            "https://friday-ai-eosin.vercel.app"
        )

    def test_06_provider_diagnostics_endpoint_safe_boolean_flags(self):
        with patch("app.config.ENV", "production"):
            with patch("app.config.GEMINI_API_KEY", "test-secret-key"):
                with patch("app.config.OPENROUTER_API_KEY", ""):
                    response = self.client.get("/health/provider-diagnostics")
                    self.assertEqual(response.status_code, 200)
                    data = response.json()
                    self.assertEqual(data["environment"], "production")
                    self.assertEqual(data["selected_provider"], "gemini")
                    self.assertTrue(data["provider_available"])
                    self.assertTrue(data["gemini_configured"])
                    self.assertFalse(data["openrouter_configured"])
                    # Ensure raw secrets are NEVER leaked in response JSON
                    self.assertNotIn("test-secret-key", str(data))


if __name__ == "__main__":
    unittest.main()

