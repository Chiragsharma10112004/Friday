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

    def test_07_provider_failure_produces_safe_diagnostics_without_leaking_key(self):
        secret_key = "sk-or-v1-secret-token-998877"
        with patch("app.config.OPENROUTER_API_KEY", secret_key):
            with patch("app.config.ENV", "production"):
                prov = OpenRouterProvider()

                # Mock OpenAI client raising an API error containing the secret key
                mock_err = Exception(f"OpenRouter 402 Payment Required: insufficient credits. Key={secret_key}")
                mock_err.status_code = 402

                with patch("app.core.providers.openrouter.OpenAI") as mock_openai:
                    mock_instance = MagicMock()
                    mock_instance.chat.completions.create.side_effect = mock_err
                    mock_openai.return_value = mock_instance

                    with self.assertLogs("friday.brain", level="WARNING") as captured_brain_logs:
                        with self.assertRaises(RuntimeError):
                            process_message(
                                messages=[{"role": "user", "content": "Hello"}],
                                preferred_provider="openrouter",
                                task="general"
                            )

                    combined_logs = " ".join(captured_brain_logs.output)
                    # Verify diagnostic details are captured
                    self.assertIn("openrouter", combined_logs)
                    self.assertIn("status=402", combined_logs)
                    self.assertIn("model=", combined_logs)
                    self.assertIn("insufficient credits", combined_logs)
                    # Verify key is strictly redacted and NEVER leaked
                    self.assertNotIn(secret_key, combined_logs)
                    self.assertIn("[REDACTED_KEY]", combined_logs)

    def test_08_public_chat_does_not_expose_diagnostics_on_provider_failure(self):
        secret_key = "sk-or-v1-super-secret-key-123"
        with patch("app.config.OPENROUTER_API_KEY", secret_key):
            with patch("app.config.ENV", "production"):
                with patch.object(OpenRouterProvider, "generate", side_effect=RuntimeError(f"Internal 500 error with key {secret_key}")):
                    response = self.client.post("/chat", json={"message": "Hello FRIDAY"})
                    self.assertEqual(response.status_code, 200)
                    reply = response.json().get("reply", "")
                    # Response should be a safe fallback and never leak internal error or secret
                    self.assertNotIn(secret_key, reply)
                    self.assertNotIn("RuntimeError", reply)
                    self.assertNotIn("500", reply)
                    self.assertIn("standing by", reply)

    def test_09_openrouter_default_model_slug(self):
        with patch("app.config.OPENROUTER_MODEL", ""):
            prov = OpenRouterProvider()
            self.assertEqual(prov.model, "meta-llama/llama-3.3-70b-instruct")
            self.assertNotIn(":free", prov.model)


if __name__ == "__main__":
    unittest.main()


