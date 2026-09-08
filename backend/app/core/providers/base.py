import re
import logging
from abc import ABC, abstractmethod
from typing import List, Dict, Any
from typing import List, Dict, Any, Optional

logger = logging.getLogger("friday.providers")


def sanitize_provider_error(text: str, max_length: int = 500) -> str:
    """
    Sanitizes error messages by redacting API keys, bearer tokens, passwords,
    and secrets, and truncating the message to a reasonable length.
    """
    if not text:
        return ""

    sanitized = str(text)

    # Redact configured API keys if present
    try:
        from app.config import OPENROUTER_API_KEY, GEMINI_API_KEY
        if OPENROUTER_API_KEY and OPENROUTER_API_KEY.strip():
            sanitized = sanitized.replace(OPENROUTER_API_KEY.strip(), "[REDACTED_KEY]")
        if GEMINI_API_KEY and GEMINI_API_KEY.strip():
            sanitized = sanitized.replace(GEMINI_API_KEY.strip(), "[REDACTED_KEY]")
    except Exception:
        pass

    # Redact common key / token patterns
    sanitized = re.sub(r'Bearer\s+[A-Za-z0-9_\-\.\~+/]+', 'Bearer [REDACTED_KEY]', sanitized, flags=re.IGNORECASE)
    sanitized = re.sub(r'sk-[A-Za-z0-9_\-\.]+', '[REDACTED_KEY]', sanitized)
    sanitized = re.sub(r'AIza[0-9A-Za-z-_]{35}', '[REDACTED_KEY]', sanitized)
    sanitized = re.sub(r'key=[A-Za-z0-9_\-]+', 'key=[REDACTED_KEY]', sanitized, flags=re.IGNORECASE)
    sanitized = re.sub(r'(?:api[_-]?key|authorization|secret|password)\s*[:=]\s*["\']?[A-Za-z0-9_\-\.]+["\']?', 'key=[REDACTED_KEY]', sanitized, flags=re.IGNORECASE)

    # Truncate if too long
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length] + "... [truncated]"

    return sanitized


def extract_provider_error_details(
    err: Exception,
    provider_name: str = "openrouter",
    model: Optional[str] = None,
    task: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Extracts structured diagnostic details from an exception safely without leaking credentials.
    """
    exc_type = type(err).__name__

    # Extract status code if available
    status_code = getattr(err, "status_code", None)
    if not status_code and hasattr(err, "response"):
        resp = err.response
        status_code = getattr(resp, "status_code", None)

    # Extract error body/message if available
    body_msg = None
    body = getattr(err, "body", None)
    if body and isinstance(body, dict):
        err_obj = body.get("error")
        if isinstance(err_obj, dict):
            body_msg = err_obj.get("message")
        elif err_obj:
            body_msg = str(err_obj)

    raw_detail = body_msg or str(err)
    safe_detail = sanitize_provider_error(raw_detail, max_length=500)

    return {
        "provider": provider_name,
        "task": task or "general",
        "model": model,
        "exception_type": exc_type,
        "status_code": status_code,
        "detail": safe_detail,
    }


class BaseAIProvider(ABC):
    """
    Abstract base class for all FRIDAY AI providers.
    """

    @abstractmethod
    def generate(
        self,
        messages: List[Dict[str, str]],
        memory_context: str = "",
        **kwargs: Any
    ) -> str:
        """
        Generate a text response given a list of chat messages and optional context.
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """
        Check if the provider is configured and available for generation.
        """
        pass

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """
        Unique identifier for the provider (e.g. 'ollama', 'gemini', 'openrouter').
        """
        pass

