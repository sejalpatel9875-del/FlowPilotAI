import os
import uuid
import httpx
from typing import AsyncGenerator, Dict, Any, List, Optional
from app.services.llm.base import BaseLLMProvider, LLMResponse, LLMTokenUsage
from app.services.llm.local_provider import LocalLLMProvider


class AnthropicProvider(BaseLLMProvider):
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self.fallback = LocalLLMProvider()

    @property
    def provider_name(self) -> str:
        return "anthropic"

    async def generate(
        self,
        prompt: str,
        model: str = "claude-3-5-sonnet-20240620",
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        **kwargs
    ) -> LLMResponse:
        if not self.api_key:
            return await self.fallback.generate(prompt, model=model, system_prompt=system_prompt)

        req_id = f"req_ant_{uuid.uuid4().hex[:12]}"
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
        payload = {
            "model": model,
            "max_tokens": max_tokens,
            "messages": [{"role": "user", "content": prompt}],
        }
        if system_prompt:
            payload["system"] = system_prompt

        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post("https://api.anthropic.com/v1/messages", headers=headers, json=payload)
            if resp.status_code != 200:
                return await self.fallback.generate(prompt, model=model, system_prompt=system_prompt)

            data = resp.json()
            content = data["content"][0]["text"]
            usage_data = data.get("usage", {})

            usage = LLMTokenUsage(
                prompt_tokens=usage_data.get("input_tokens", 0),
                completion_tokens=usage_data.get("output_tokens", 0),
                total_tokens=usage_data.get("input_tokens", 0) + usage_data.get("output_tokens", 0),
                estimated_cost_usd=0.003,
            )

            return LLMResponse(
                text=content,
                provider="anthropic",
                model=model,
                usage=usage,
                request_id=req_id,
            )

    async def stream(
        self,
        prompt: str,
        model: str = "claude-3-5-sonnet-20240620",
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        async for token in self.fallback.stream(prompt, model=model):
            yield token

    async def structured_output(
        self,
        prompt: str,
        response_schema: Dict[str, Any],
        model: str = "claude-3-5-sonnet-20240620",
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        return await self.fallback.structured_output(prompt, response_schema, model=model)

    async def embed(self, text: str, model: str = "text-embedding-3-small") -> List[float]:
        return await self.fallback.embed(text, model=model)
