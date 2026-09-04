from typing import List, Dict, Any
import requests
import json

from app.config import GEMINI_API_KEY, GEMINI_MODEL
from app.core.providers.base import BaseAIProvider

SYSTEM_PROMPT = """
You are FRIDAY, an Autonomous AI Personal Operating System.

Be intelligent, concise, proactive, accurate, and helpful.
When answering the user, use the provided memory context, profile, and conversation history.
If a user name, fact, or detail has not been stored or provided in memory or context, state that it is not provided rather than guessing or hallucinating.
"""


class GeminiProvider(BaseAIProvider):
    """
    Google Gemini AI provider supporting both Google GenAI SDK and REST API.
    """

    def __init__(self, api_key: str = None, model: str = None):
        self.api_key = api_key or GEMINI_API_KEY
        self.model = model or GEMINI_MODEL

    @property
    def provider_name(self) -> str:
        return "gemini"

    def is_available(self) -> bool:
        return bool(self.api_key and self.api_key.strip())

    def generate(
        self,
        messages: List[Dict[str, str]],
        memory_context: str = "",
        **kwargs: Any
    ) -> str:
        if not self.is_available():
            raise ValueError("Gemini API key is not configured.")

        system_instruction = SYSTEM_PROMPT.strip()
        if memory_context:
            system_instruction += "\n\n" + memory_context

        # Try Google GenAI SDK first if installed
        try:
            from google import genai
            client = genai.Client(api_key=self.api_key)
            
            prompt_parts = []
            for msg in messages:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                if role == "system":
                    system_instruction += "\n\n" + content
                else:
                    prompt_parts.append(f"{role.upper()}: {content}")
            
            combined_prompt = "\n\n".join(prompt_parts)
            
            response = client.models.generate_content(
                model=self.model,
                contents=combined_prompt,
                config={
                    "system_instruction": system_instruction,
                    "temperature": kwargs.get("temperature", 0.7),
                }
            )
            if response and response.text:
                return response.text
        except ImportError:
            pass
        except Exception:
            pass

        # Fallback to direct Gemini REST API
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
        
        contents = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role == "system":
                system_instruction += "\n\n" + content
            else:
                gemini_role = "model" if role == "assistant" else "user"
                contents.append({
                    "role": gemini_role,
                    "parts": [{"text": content}]
                })

        payload = {
            "contents": contents,
            "systemInstruction": {
                "parts": [{"text": system_instruction}]
            },
            "generationConfig": {
                "temperature": kwargs.get("temperature", 0.7),
            }
        }

        try:
            resp = requests.post(
                url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            if resp.status_code != 200:
                error_msg = f"Gemini API returned status {resp.status_code}"
                try:
                    err_json = resp.json()
                    if "error" in err_json and "message" in err_json["error"]:
                        error_msg += f": {err_json['error']['message']}"
                except Exception:
                    pass
                raise RuntimeError(error_msg)

            data = resp.json()
            candidates = data.get("candidates", [])
            if not candidates:
                raise RuntimeError("Gemini returned empty candidate response.")
            
            parts = candidates[0].get("content", {}).get("parts", [])
            if not parts:
                raise RuntimeError("Gemini returned empty content parts.")

            return parts[0].get("text", "").strip()

        except Exception as err:
            raise RuntimeError(f"Gemini generation failed ({self.model}): {str(err)}") from err

