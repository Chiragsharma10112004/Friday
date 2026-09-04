from typing import List, Dict, Any
from openai import OpenAI

from app.config import OPENROUTER_API_KEY, OPENROUTER_MODEL
from app.core.providers.base import BaseAIProvider

SYSTEM_PROMPT = """
You are FRIDAY, an Autonomous AI Personal Operating System.

Be intelligent, concise, proactive, accurate, and helpful.
When answering the user, use the provided memory context, profile, and conversation history.
If a user name, fact, or detail has not been stored or provided in memory or context, state that it is not provided rather than guessing or hallucinating.
"""


class OpenRouterProvider(BaseAIProvider):
    """
    OpenRouter API provider using the OpenAI client.
    """

    def __init__(self, api_key: str = None, model: str = None):
        self.api_key = api_key or OPENROUTER_API_KEY
        self.model = model or OPENROUTER_MODEL

    @property
    def provider_name(self) -> str:
        return "openrouter"

    def is_available(self) -> bool:
        return bool(self.api_key and self.api_key.strip())

    def generate(
        self,
        messages: List[Dict[str, str]],
        memory_context: str = "",
        **kwargs: Any
    ) -> str:
        if not self.is_available():
            raise ValueError("OpenRouter API key is not configured.")

        system_content = SYSTEM_PROMPT.strip()
        if memory_context:
            system_content += "\n\n" + memory_context

        formatted_messages = [
            {"role": "system", "content": system_content},
            *messages
        ]

        try:
            client = OpenAI(
                api_key=self.api_key,
                base_url="https://openrouter.ai/api/v1",
                timeout=30.0,
                max_retries=1
            )
            response = client.chat.completions.create(
                model=self.model,
                messages=formatted_messages,
                temperature=kwargs.get("temperature", 0.7),
                max_tokens=kwargs.get("max_tokens", 2048),
                timeout=30.0
            )
            return response.choices[0].message.content
        except Exception as err:
            raise RuntimeError(f"OpenRouter generation failed ({self.model}): {str(err)}") from err


# Backward compatibility wrapper
_default_openrouter = OpenRouterProvider()

def chat(message: str) -> str:
    return _default_openrouter.generate([{"role": "user", "content": message}])
