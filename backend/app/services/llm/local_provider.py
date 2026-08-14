import uuid
import json
import asyncio
from typing import AsyncGenerator, Dict, Any, List, Optional
from app.services.llm.base import BaseLLMProvider, LLMResponse, LLMTokenUsage


class LocalLLMProvider(BaseLLMProvider):
    @property
    def provider_name(self) -> str:
        return "local"

    async def generate(
        self,
        prompt: str,
        model: str = "flowpilot-local-v1",
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        **kwargs
    ) -> LLMResponse:
        req_id = f"req_loc_{uuid.uuid4().hex[:12]}"
        prompt_words = len(prompt.split())
        
        reply_text = (
            f"[FlowPilot AI Engine Engine Response]\n\n"
            f"Query Analyzed: '{prompt}'\n"
            f"Model: {model} (Local Development Provider)\n"
            f"Recommended Focus: Proceed with priority lead outreach and project milestone verification."
        )
        completion_words = len(reply_text.split())

        usage = LLMTokenUsage(
            prompt_tokens=prompt_words * 2,
            completion_tokens=completion_words * 2,
            total_tokens=(prompt_words + completion_words) * 2,
            estimated_cost_usd=0.0,
        )

        return LLMResponse(
            text=reply_text,
            provider="local",
            model=model,
            usage=usage,
            request_id=req_id,
        )

    async def stream(
        self,
        prompt: str,
        model: str = "flowpilot-local-v1",
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        tokens = [
            "[FlowPilot ", "AI ", "Engine] ", "Analyzing ", "query: ", f"'{prompt}'...\n\n",
            "1. ", "Lead ", "Scoring: ", "Identified ", "high-value ", "prospects.\n",
            "2. ", "Next ", "Step: ", "Dispatch ", "automated ", "follow-ups."
        ]
        for token in tokens:
            await asyncio.sleep(0.05)
            yield token

    async def structured_output(
        self,
        prompt: str,
        response_schema: Dict[str, Any],
        model: str = "flowpilot-local-v1",
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        return {
            "suggestedAction": f"Execute action plan for: {prompt[:40]}...",
            "confidenceScore": 0.95,
            "recommendedSteps": [
                {"title": "Step 1", "description": "Qualify leads in database"},
                {"title": "Step 2", "description": "Review client deadlines"}
            ]
        }

    async def embed(self, text: str, model: str = "text-embedding-3-small") -> List[float]:
        # Return deterministic dummy vector of length 1536
        return [0.01 * (i % 10) for i in range(1536)]
