from typing import List, Dict, Any
import requests
import json

from app.config import OLLAMA_MODEL, OLLAMA_BASE_URL
from app.core.providers.base import BaseAIProvider

SYSTEM_PROMPT = """
You are FRIDAY, an Autonomous AI Personal Operating System.

Never say you are Qwen or another underlying model. You are FRIDAY.

Be intelligent, concise, proactive, accurate, and helpful.
When answering the user, use the provided memory context, profile, and conversation history.
If a user name, fact, or detail has not been stored or provided in memory or context, state that it is not provided rather than guessing or hallucinating.
"""


class OllamaProvider(BaseAIProvider):
    """
    Ollama local model provider.
    """

    def __init__(self, model: str = None, base_url: str = None):
        self.model = model or OLLAMA_MODEL
        self.base_url = (base_url or OLLAMA_BASE_URL).rstrip("/")

    @property
    def provider_name(self) -> str:
        return "ollama"

    def is_available(self) -> bool:
        """
        Check if Ollama service is reachable.
        """
        try:
            url = self.base_url.replace("localhost", "127.0.0.1")
            resp = requests.get(f"{url}/api/tags", timeout=0.5)
            return resp.status_code == 200
        except Exception:
            return False

    def generate(
        self,
        messages: List[Dict[str, str]],
        memory_context: str = "",
        **kwargs: Any
    ) -> str:
        if not self.is_available():
            raise RuntimeError(f"Ollama service is not reachable at {self.base_url}")

        formatted_messages = [
            {
                "role": "system",
                "content": SYSTEM_PROMPT.strip() + ("\n\n" + memory_context if memory_context else "")
            },
            *messages
        ]

        # Try native ollama package if installed
        try:
            import ollama
            response = ollama.chat(
                model=self.model,
                messages=formatted_messages
            )
            return response["message"]["content"]
        except ImportError:
            pass
        except Exception:
            pass

        # Fallback to direct HTTP API
        try:
            resp = requests.post(
                f"{self.base_url}/api/chat",
                json={
                    "model": self.model,
                    "messages": formatted_messages,
                    "stream": False
                },
                timeout=30
            )
            resp.raise_for_status()
            data = resp.json()
            return data["message"]["content"]
        except Exception as err:
            raise RuntimeError(f"Ollama generation failed ({self.model}): {str(err)}") from err


# Backward compatibility wrapper
_default_ollama = OllamaProvider()

def generate(messages: List[Dict[str, str]], memory_context: str = "") -> str:
    return _default_ollama.generate(messages, memory_context)
