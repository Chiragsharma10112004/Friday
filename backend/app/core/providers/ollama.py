from typing import List, Dict, Any
import requests
import json

from app.config import OLLAMA_MODEL, OLLAMA_BASE_URL
from app.core.providers.base import BaseAIProvider

SYSTEM_PROMPT = """
You are FRIDAY.

Never say you are Qwen.

You are Chirag's personal AI assistant.

Be intelligent, concise, proactive and helpful.
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
            resp = requests.get(f"{self.base_url}/api/tags", timeout=2)
            return resp.status_code == 200
        except Exception:
            return False

    def generate(
        self,
        messages: List[Dict[str, str]],
        memory_context: str = "",
        **kwargs: Any
    ) -> str:
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
        except Exception as e:
            # Fall back to direct REST API if Python package fails
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
                timeout=120
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
