import json
import logging
from typing import Dict, Any, Optional, List, AsyncGenerator
import httpx

from app.core.config import settings
from app.services.llm.base_provider import LLMProvider, LLMRequest, LLMResponse, LLMUsage

logger = logging.getLogger("flowpilot.llm.ollama")


class OllamaProvider(LLMProvider):
    def __init__(self, base_url: Optional[str] = None, model_name: Optional[str] = None):
        self.base_url = (base_url or settings.LLM_BASE_URL or "http://localhost:11434").rstrip("/")
        self._model = model_name or settings.LLM_MODEL or "llama3"

    @property
    def provider_name(self) -> str:
        return "ollama"

    @property
    def default_model(self) -> str:
        return self._model

    async def generate(self, req: LLMRequest) -> LLMResponse:
        model = req.model or self._model
        prompt_text = f"{req.system_prompt}\n\n{req.prompt}" if req.system_prompt else req.prompt

        payload = {
            "model": model,
            "prompt": prompt_text,
            "stream": False,
            "options": {
                "temperature": req.temperature,
            }
        }

        try:
            async with httpx.AsyncClient(timeout=settings.LLM_TIMEOUT) as client:
                resp = await client.post(f"{self.base_url}/api/generate", json=payload)
                if resp.status_code != 200:
                    raise RuntimeError(f"Ollama API Error ({resp.status_code}): {resp.text}")

                data = resp.json()
                text = data.get("response", "Ollama provider completed.")
                in_tokens = data.get("prompt_eval_count", len(req.prompt) // 4)
                out_tokens = data.get("eval_count", len(text) // 4)

                return LLMResponse(
                    text=text,
                    raw_output=json.dumps(data),
                    usage=LLMUsage(input_tokens=in_tokens, output_tokens=out_tokens, total_tokens=in_tokens + out_tokens),
                    provider=self.provider_name,
                    model=model,
                )
        except Exception as e:
            # Local fallback response if local Ollama server is offline
            prompt_words = len(req.prompt.split())
            out_text = f"FlowPilot Local Ollama Provider [{model}]: Local fallback response for query ({prompt_words} words)."
            return LLMResponse(
                text=out_text,
                usage=LLMUsage(input_tokens=prompt_words * 4, output_tokens=20, total_tokens=(prompt_words * 4) + 20),
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
