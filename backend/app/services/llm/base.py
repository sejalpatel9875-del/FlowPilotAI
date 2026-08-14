from abc import ABC, abstractmethod
from typing import AsyncGenerator, Dict, Any, List, Optional
from pydantic import BaseModel, Field


class LLMTokenUsage(BaseModel):
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    estimated_cost_usd: float = 0.0


class LLMResponse(BaseModel):
    text: str
    provider: str
    model: str
    usage: LLMTokenUsage
    request_id: str
    raw_response: Optional[Dict[str, Any]] = None


class BaseLLMProvider(ABC):
    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Returns unique string name of provider (openai, anthropic, gemini, local)."""
        pass

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        model: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        **kwargs
    ) -> LLMResponse:
        """Generate a complete text response."""
        pass

    @abstractmethod
    async def stream(
        self,
        prompt: str,
        model: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """Stream response tokens sequentially."""
        pass

    @abstractmethod
    async def structured_output(
        self,
        prompt: str,
        response_schema: Dict[str, Any],
        model: str,
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Generate valid JSON matching a target schema."""
        pass

    @abstractmethod
    async def embed(self, text: str, model: str = "text-embedding-3-small") -> List[float]:
        """Generate text vector embeddings."""
        pass
