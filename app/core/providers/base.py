from abc import ABC, abstractmethod
from typing import List, Dict, Any


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

