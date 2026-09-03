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


def get_provider(provider_name: Optional[str] = None, task: Optional[str] = None) -> BaseAIProvider:
    """
    Resolve the AI provider to use based on requested name, task, or configuration.
    """
    if provider_name:
        selected_name = provider_name.lower().strip()
    elif task == "job_analysis":
        selected_name = JOB_ANALYSIS_PROVIDER.lower().strip()
    else:
        selected_name = DEFAULT_AI_PROVIDER.lower().strip()

    provider = _PROVIDERS.get(selected_name)
    if provider:
        return provider

    # Fallback to default or ollama
    return _PROVIDERS.get(DEFAULT_AI_PROVIDER, _PROVIDERS["ollama"])


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

    # Fallback chain: try other available providers
    fallback_candidates = [
        name for name, prov in _PROVIDERS.items()
        if name != primary_name and prov.is_available()
    ]

    # Ensure local ollama is always in the candidate list as the ultimate fallback
    if "ollama" not in fallback_candidates and primary_name != "ollama":
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
