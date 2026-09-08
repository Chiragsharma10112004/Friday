import logging
from typing import List, Dict, Any, Optional

from app.config import (
    DEFAULT_AI_PROVIDER,
    JOB_ANALYSIS_PROVIDER,
)
from app.core.providers.base import BaseAIProvider
from app.core.providers.ollama import OllamaProvider
from app.core.providers.gemini import GeminiProvider
from app.core.providers.openrouter import OpenRouterProvider

logger = logging.getLogger("friday.brain")

# Registry of supported providers
_PROVIDERS: Dict[str, BaseAIProvider] = {
    "ollama": OllamaProvider(),
    "gemini": GeminiProvider(),
    "openrouter": OpenRouterProvider(),
}


def resolve_best_provider_name(provider_name: Optional[str] = None, task: Optional[str] = None) -> str:
    """
    Intelligently select the best AI provider name based on explicit request,
    task configuration, environment (dev vs prod), and configured API keys.
    """
    from app.config import (
        DEFAULT_AI_PROVIDER,
        JOB_ANALYSIS_PROVIDER,
        OPENROUTER_API_KEY,
        GEMINI_API_KEY,
    )

    if provider_name:
        req = provider_name.lower().strip()
        if req in _PROVIDERS:
            return req

    if task == "job_analysis" and JOB_ANALYSIS_PROVIDER:
        job_prov = JOB_ANALYSIS_PROVIDER.lower().strip()
        if job_prov in _PROVIDERS and _PROVIDERS[job_prov].is_available():
            return job_prov

    configured_default = (DEFAULT_AI_PROVIDER or "ollama").lower().strip()

    # If the user explicitly configured openrouter or gemini, and key is available
    if configured_default in ("openrouter", "gemini") and _PROVIDERS[configured_default].is_available():
        return configured_default

    # In production or when default provider is offline:
    # Automatically route to configured cloud providers
    if OPENROUTER_API_KEY and OPENROUTER_API_KEY.strip():
        return "openrouter"
    if GEMINI_API_KEY and GEMINI_API_KEY.strip():
        return "gemini"

    # In local development, try configured default (e.g. ollama)
    if configured_default in _PROVIDERS and _PROVIDERS[configured_default].is_available():
        return configured_default

    return configured_default if configured_default in _PROVIDERS else "ollama"


def get_provider(provider_name: Optional[str] = None, task: Optional[str] = None) -> BaseAIProvider:
    """
    Resolve the AI provider to use based on requested name, task, or configuration.
    """
    selected_name = resolve_best_provider_name(provider_name=provider_name, task=task)
    return _PROVIDERS.get(selected_name, _PROVIDERS["ollama"])


def process_message(
    messages: List[Dict[str, str]],
    memory_context: str = "",
    task: Optional[str] = None,
    preferred_provider: Optional[str] = None,
    **kwargs: Any
) -> str:
    """
    Central AI generation function for FRIDAY.
    Dispatches to the configured primary provider with safe fallback.
    """
    primary_provider = get_provider(provider_name=preferred_provider, task=task)
    primary_name = primary_provider.provider_name

    # Check if primary provider is available
    if primary_provider.is_available():
        try:
            return primary_provider.generate(
                messages=messages,
                memory_context=memory_context,
                **kwargs
            )
        except Exception as err:
            logger.warning(
                "Primary AI provider '%s' failed for task '%s': %s. Attempting fallback.",
                primary_name,
                task or "general",
                type(err).__name__
            )
    else:
        logger.info(
            "Primary AI provider '%s' is not configured/available for task '%s'. Attempting fallback.",
            primary_name,
            task or "general"
        )

    # Fallback chain: prioritize cloud providers first, then local development
    fallback_order = ["openrouter", "gemini", "ollama"]
    fallback_candidates = [
        name for name in fallback_order
        if name != primary_name and name in _PROVIDERS and _PROVIDERS[name].is_available()
    ]

    # In local development only, if no available fallback candidates found, try ollama
    from app.config import ENV
    if ENV != "production" and not fallback_candidates and primary_name != "ollama":
        fallback_candidates.append("ollama")

    for fallback_name in fallback_candidates:
        fallback_provider = _PROVIDERS[fallback_name]
        try:
            logger.info(
                "Using fallback provider '%s' for task '%s'.",
                fallback_name,
                task or "general"
            )
            return fallback_provider.generate(
                messages=messages,
                memory_context=memory_context,
                **kwargs
            )
        except Exception as fallback_err:
            logger.warning(
                "Fallback provider '%s' failed: %s",
                fallback_name,
                type(fallback_err).__name__
            )

    raise RuntimeError(
        f"All AI providers (attempted: {primary_name}, {', '.join(fallback_candidates)}) "
        f"failed to generate a response for task '{task or 'general'}'."
    )
