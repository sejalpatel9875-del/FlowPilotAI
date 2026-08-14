from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, AsyncGenerator
from pydantic import BaseModel, Field


class LLMUsage(BaseModel):
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0


class LLMRequest(BaseModel):
    prompt: str = Field(..., description="User prompt text")
    system_prompt: Optional[str] = Field(None, description="Optional system directive")
    model: Optional[str] = Field(None, description="Target model override")
    temperature: float = Field(default=0.7, description="Generation temperature (0.0 - 1.0)")
    max_tokens: Optional[int] = Field(default=1024, description="Maximum token generation limit")
    response_format: Optional[str] = Field(default="text", description="text or json")
    json_schema: Optional[Dict[str, Any]] = Field(default=None, description="Target JSON schema structure")


class LLMResponse(BaseModel):
    text: str = Field(..., description="Generated text output")
    raw_output: Optional[str] = Field(None, description="Raw provider output string")
    usage: LLMUsage = Field(default_factory=LLMUsage, description="Token usage summary")
    provider: str = Field(..., description="Active provider name")
    model: str = Field(..., description="Active model name")
    finish_reason: str = Field(default="stop")
    metadata: Dict[str, Any] = Field(default_factory=dict)


class LLMProvider(ABC):
    @property
    @abstractmethod
    def provider_name(self) -> str:
        pass

    @property
    @abstractmethod
    def default_model(self) -> str:
        pass

    @abstractmethod
    async def generate(self, req: LLMRequest) -> LLMResponse:
        """Synchronous text generation."""
        pass

    @abstractmethod
    async def stream(self, req: LLMRequest) -> AsyncGenerator[str, None]:
        """Streaming text token generation."""
        pass

    @abstractmethod
    async def structured_output(self, req: LLMRequest, schema: Dict[str, Any]) -> LLMResponse:
        """Structured JSON schema text generation."""
        pass

    @abstractmethod
    async def embed(self, text: str) -> List[float]:
        """Generate text vector embedding."""
        pass
