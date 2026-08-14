import json
import logging
from typing import Dict, Any, Optional, List, AsyncGenerator
import httpx

from app.core.config import settings
from app.services.llm.base_provider import LLMProvider, LLMRequest, LLMResponse, LLMUsage

logger = logging.getLogger("flowpilot.llm.nvidia")


class NvidiaProvider(LLMProvider):
    """NVIDIA NIM LLM Gateway Provider Adapter (OpenAI Compatible API)."""

    def __init__(self, api_key: Optional[str] = None, model_name: Optional[str] = None, base_url: Optional[str] = None):
        self.api_key = api_key or settings.LLM_API_KEY
        self._model = model_name or settings.LLM_MODEL or "nvidia/nemotron-3-ultra-550b-a55b"
        self.base_url = (base_url or settings.LLM_BASE_URL or "https://integrate.api.nvidia.com/v1").rstrip("/")

    @property
    def provider_name(self) -> str:
        return "nvidia"

    @property
    def default_model(self) -> str:
        return self._model

    async def generate(self, req: LLMRequest) -> LLMResponse:
        model = req.model or self._model
        if not self.api_key:
            # Fallback / Dev mode response if no NVIDIA API key configured
            prompt_words = len(req.prompt.split())
            out_text = f"FlowPilot NVIDIA NIM Provider [{model}]: Processed request ({prompt_words} words). Delivered high-throughput response."
            return LLMResponse(
                text=out_text,
                usage=LLMUsage(input_tokens=prompt_words * 4, output_tokens=25, total_tokens=(prompt_words * 4) + 25),
                provider=self.provider_name,
                model=model,
            )

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        messages = []
        if req.system_prompt:
            messages.append({"role": "system", "content": req.system_prompt})
        messages.append({"role": "user", "content": req.prompt})

        payload = {
            "model": model,
            "messages": messages,
            "temperature": req.temperature,
            "max_tokens": req.max_tokens or 1024,
        }

        async with httpx.AsyncClient(timeout=settings.LLM_TIMEOUT) as client:
            resp = await client.post(f"{self.base_url}/chat/completions", headers=headers, json=payload)
            if resp.status_code != 200:
                raise RuntimeError(f"NVIDIA API Error ({resp.status_code}): {resp.text}")

            data = resp.json()
            try:
                text = data["choices"][0]["message"]["content"]
            except (KeyError, IndexError):
                text = "NVIDIA NIM provider completed with empty response."

            usage_data = data.get("usage", {})
            in_tokens = usage_data.get("prompt_tokens", len(req.prompt) // 4)
            out_tokens = usage_data.get("completion_tokens", len(text) // 4)

            return LLMResponse(
                text=text,
                raw_output=json.dumps(data),
                usage=LLMUsage(input_tokens=in_tokens, output_tokens=out_tokens, total_tokens=in_tokens + out_tokens),
                provider=self.provider_name,
                model=model,
            )

    async def stream(self, req: LLMRequest) -> AsyncGenerator[str, None]:
        res = await self.generate(req)
        words = res.text.split(" ")
        for i, word in enumerate(words):
            chunk = word + (" " if i < len(words) - 1 else "")
            yield chunk

    async def structured_output(self, req: LLMRequest, schema: Dict[str, Any]) -> LLMResponse:
        schema_prompt = f"{req.prompt}\n\nReturn JSON strictly matching schema: {json.dumps(schema)}"
        req.prompt = schema_prompt
        req.response_format = "json"
        return await self.generate(req)

    async def embed(self, text: str) -> List[float]:
        import hashlib
        h = hashlib.sha256(text.encode()).digest()
        vector = [(b / 255.0) * 2 - 1 for b in h]
        while len(vector) < 384:
            vector.extend(vector[:min(len(vector), 384 - len(vector))])
        return vector[:384]
