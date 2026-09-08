import logging
from typing import List, Dict, Any, Optional

from app.core.providers.base import BaseAIProvider
from app.core.providers.base import BaseAIProvider, extract_provider_error_details
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


def resolve_best_provider_name(
    provider_name: Optional[str] = None,
    task: Optional[str] = None,
) -> str:
    """
    Resolve the best AI provider based on explicit preference,
    task configuration, environment, and provider availability.
    """
    from app.config import (
        ENV,
        DEFAULT_AI_PROVIDER,
        JOB_ANALYSIS_PROVIDER,
        OPENROUTER_API_KEY,
        GEMINI_API_KEY,
    )

    if provider_name:
        requested = provider_name.lower().strip()
        if requested in _PROVIDERS:
            return requested

    if task == "job_analysis" and JOB_ANALYSIS_PROVIDER:
        job_prov = JOB_ANALYSIS_PROVIDER.lower().strip()
        if job_prov in _PROVIDERS and _PROVIDERS[job_prov].is_available():
            return job_prov

    configured_default = (DEFAULT_AI_PROVIDER or "ollama").lower().strip()

    # Respect an explicitly configured cloud provider when available
    if configured_default in ("gemini", "openrouter") and _PROVIDERS[configured_default].is_available():
        return configured_default

    # Production/cloud environments should prefer configured cloud providers
    if ENV == "production":
        if OPENROUTER_API_KEY and OPENROUTER_API_KEY.strip():
            return "openrouter"
        if GEMINI_API_KEY and GEMINI_API_KEY.strip():
            return "gemini"
        for name in ("gemini", "openrouter"):
            if _PROVIDERS[name].is_available():
                return name
        return configured_default if configured_default in ("gemini", "openrouter") else "openrouter"

    # Local development: use the configured provider if available
    if configured_default in _PROVIDERS and _PROVIDERS[configured_default].is_available():
        return configured_default

    # Local fallback order
    for name in ("gemini", "openrouter", "ollama"):
        if _PROVIDERS[name].is_available():
            return name

    return configured_default if configured_default in _PROVIDERS else "ollama"


def get_provider(
    provider_name: Optional[str] = None,
    task: Optional[str] = None,
) -> BaseAIProvider:
    """
    Resolve the AI provider to use based on requested name, task, or configuration.
    """
    selected_name = resolve_best_provider_name(
        provider_name=provider_name,
        task=task,
    )
    return _PROVIDERS.get(selected_name, _PROVIDERS["ollama"])


def process_message(
    messages: List[Dict[str, str]],
    memory_context: str = "",
    task: Optional[str] = None,
    preferred_provider: Optional[str] = None,
    **kwargs: Any,
) -> str:
    """
    Central AI generation function for FRIDAY.
    Dispatches to the configured primary provider with safe fallback.
    """
    primary_provider = get_provider(
        provider_name=preferred_provider,
        task=task,
    )
    primary_name = primary_provider.provider_name

    # Check if primary provider is available
    if primary_provider.is_available():
        try:
            return primary_provider.generate(
                messages=messages,
                memory_context=memory_context,
                task=task,
                **kwargs,
            )
        except Exception as err:
            details = extract_provider_error_details(
                err=err,
                provider_name=primary_name,
                model=getattr(primary_provider, "model", None),
                task=task or "general",
            )
            status_info = f", status={details['status_code']}" if details['status_code'] else ""
            model_info = f", model={details['model']}" if details['model'] else ""
            logger.warning(
                "Primary AI provider '%s' failed for task '%s' (type=%s%s%s): %s. Attempting fallback.",
                primary_name,
                task or "general",
                details["exception_type"],
                model_info,
                status_info,
                details["detail"],
            )
    else:
        logger.info(
            "Primary AI provider '%s' is not configured/available for task '%s'. Attempting fallback.",
            primary_name,
            task or "general",
        )

    # Fallback chain: prioritize cloud providers first, then local development
    fallback_order = ["gemini", "openrouter", "ollama"]

    fallback_candidates = [
        name
        for name in fallback_order
        if name != primary_name
        and name in _PROVIDERS
        and _PROVIDERS[name].is_available()
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
                task or "general",
            )
            return fallback_provider.generate(
                messages=messages,
                memory_context=memory_context,
                task=task,
                **kwargs,
            )
        except Exception as fallback_err:
            fb_details = extract_provider_error_details(
                err=fallback_err,
                provider_name=fallback_name,
                model=getattr(fallback_provider, "model", None),
                task=task or "general",
            )
            fb_status_info = f", status={fb_details['status_code']}" if fb_details['status_code'] else ""
            fb_model_info = f", model={fb_details['model']}" if fb_details['model'] else ""
            logger.warning(
                "Fallback provider '%s' failed for task '%s' (type=%s%s%s): %s",
                fallback_name,
                task or "general",
                fb_details["exception_type"],
                fb_model_info,
                fb_status_info,
                fb_details["detail"],
            )

    raise RuntimeError(
        f"All AI providers (attempted: {primary_name}, "
        f"{', '.join(fallback_candidates)}) failed to generate a response "
        f"for task '{task or 'general'}'."
    )

