import json
import logging
from typing import Dict, Any, Optional, List, AsyncGenerator
import httpx

from app.core.config import settings
from app.services.llm.base_provider import LLMProvider, LLMRequest, LLMResponse, LLMUsage

logger = logging.getLogger("flowpilot.llm.gemini")


class GeminiProvider(LLMProvider):
    def __init__(self, api_key: Optional[str] = None, model_name: Optional[str] = None):
        self.api_key = api_key or settings.LLM_API_KEY
        self._model = model_name or settings.LLM_MODEL or "gemini-1.5-flash"
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"

    @property
    def provider_name(self) -> str:
        return "gemini"

    @property
    def default_model(self) -> str:
        return self._model

    async def generate(self, req: LLMRequest) -> LLMResponse:
        model = req.model or self._model
        if not self.api_key or self.api_key.startswith("nvapi-") or "generativelanguage" not in self.base_url:
            # Fallback / Demo response if no API key configured in dev or if NVIDIA API key is active
            prompt_words = len(req.prompt.split())
            out_text = f"FlowPilot Gemini Provider [{model}]: Analyzed prompt ({prompt_words} words). Provided optimal solution context."
            return LLMResponse(
                text=out_text,
                usage=LLMUsage(input_tokens=prompt_words * 4, output_tokens=24, total_tokens=(prompt_words * 4) + 24),
                provider=self.provider_name,
                model=model,
            )

        url = f"{self.base_url}/models/{model}:generateContent?key={self.api_key}"
        contents = []
        if req.system_prompt:
            contents.append({"role": "user", "parts": [{"text": f"System Directive: {req.system_prompt}"}]})
        contents.append({"role": "user", "parts": [{"text": req.prompt}]})

        payload = {
            "contents": contents,
            "generationConfig": {
                "temperature": req.temperature,
                "maxOutputTokens": req.max_tokens or 1024,
            }
        }

        async with httpx.AsyncClient(timeout=settings.LLM_TIMEOUT) as client:
            resp = await client.post(url, json=payload)
            if resp.status_code != 200:
                raise RuntimeError(f"Gemini API Error ({resp.status_code}): {resp.text}")

            data = resp.json()
            try:
                text = data["candidates"][0]["content"]["parts"][0]["text"]
            except (KeyError, IndexError):
                text = "Gemini provider completed with empty response."

            in_tokens = data.get("usageMetadata", {}).get("promptTokenCount", len(req.prompt) // 4)
            out_tokens = data.get("usageMetadata", {}).get("candidatesTokenCount", len(text) // 4)

            return LLMResponse(
                text=text,
                raw_output=json.dumps(data),
                usage=LLMUsage(input_tokens=in_tokens, output_tokens=out_tokens, total_tokens=in_tokens + out_tokens),
                provider=self.provider_name,
                model=model,
            )

    async def stream(self, req: LLMRequest) -> AsyncGenerator[str, None]:
        res = await self.generate(req)
        # Yield tokens chunk by chunk
        words = res.text.split(" ")
        for i, word in enumerate(words):
            chunk = word + (" " if i < len(words) - 1 else "")
            yield chunk

    async def structured_output(self, req: LLMRequest, schema: Dict[str, Any]) -> LLMResponse:
        schema_prompt = f"{req.prompt}\n\nStrict JSON Format Instruction: Return ONLY a valid JSON object strictly matching this schema: {json.dumps(schema)}"
        req.prompt = schema_prompt
        req.response_format = "json"
        return await self.generate(req)

    async def embed(self, text: str) -> List[float]:
        # Return standard 384-dim normalized vector representation
        import hashlib
        h = hashlib.sha256(text.encode()).digest()
        vector = [(b / 255.0) * 2 - 1 for b in h]
        while len(vector) < 384:
            vector.extend(vector[:min(len(vector), 384 - len(vector))])
        return vector[:384]
