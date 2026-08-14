import logging
from typing import Dict, Type, Optional
from app.services.llm.base_provider import LLMProvider
from app.services.llm.gemini_provider import GeminiProvider
from app.services.llm.openai_provider import OpenAIProvider
from app.services.llm.ollama_provider import OllamaProvider
from app.services.llm.nvidia_provider import NvidiaProvider

logger = logging.getLogger("flowpilot.llm.registry")


class LLMProviderRegistry:
    def __init__(self):
        self._providers: Dict[str, LLMProvider] = {
            "gemini": GeminiProvider(),
            "openai": OpenAIProvider(),
            "ollama": OllamaProvider(),
            "nvidia": NvidiaProvider(),
        }

    def get_provider(self, name: str) -> LLMProvider:
        key = (name or "").lower().strip()
        if key not in self._providers:
            available = list(self._providers.keys())
            raise ValueError(f"Unsupported LLM Provider '{name}'. Supported providers: {available}")
        return self._providers[key]

    def register_provider(self, name: str, provider_instance: LLMProvider):
        self._providers[name.lower().strip()] = provider_instance


# Global registry singleton
llm_provider_registry = LLMProviderRegistry()
