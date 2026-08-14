import time
import uuid
import logging
from typing import AsyncGenerator, Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.llm.base import BaseLLMProvider, LLMResponse, LLMTokenUsage
from app.services.llm.openai_provider import OpenAIProvider
from app.services.llm.anthropic_provider import AnthropicProvider
from app.services.llm.gemini_provider import GeminiProvider
from app.services.llm.local_provider import LocalLLMProvider
from app.models.ai_gateway import AIRequestLogModel, AIUsageModel

logger = logging.getLogger("flowpilot.ai_service")


class AIService:
    def __init__(self):
        # Register available providers
        self.providers: Dict[str, BaseLLMProvider] = {
            "openai": OpenAIProvider(),
            "anthropic": AnthropicProvider(),
            "gemini": GeminiProvider(),
            "local": LocalLLMProvider(),
        }
        self.default_provider = "local"

    def get_provider(self, provider_name: Optional[str] = None) -> BaseLLMProvider:
        name = (provider_name or self.default_provider).lower()
        return self.providers.get(name, self.providers["local"])

    def validate_ai_policy(self, prompt: str):
        """AI policy check: block malicious or empty inputs."""
        if not prompt or not prompt.strip():
            raise ValueError("Prompt input cannot be empty.")
        if len(prompt) > 20000:
            raise ValueError("Prompt exceeds maximum length policy (20,000 characters).")

    async def generate_response(
        self,
        prompt: str,
        user_id: str,
        db: AsyncSession,
        provider: str = "local",
        model: str = "flowpilot-local-v1",
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        fallback_provider: str = "local",
    ) -> LLMResponse:
        self.validate_ai_policy(prompt)
        request_id = f"req_{uuid.uuid4().hex[:14]}"
        start_time = time.time()
        
        target_provider = self.get_provider(provider)
        status_str = "success"

        try:
            # Primary provider attempt with timeout
            response = await target_provider.generate(
                prompt=prompt,
                model=model,
                system_prompt=system_prompt,
                temperature=temperature,
                max_tokens=max_tokens,
            )
        except Exception as e:
            logger.warning(f"Primary provider '{provider}' failed ({str(e)}). Executing fallback to '{fallback_provider}'.")
            status_str = "fallback"
            fallback_adapter = self.get_provider(fallback_provider)
            response = await fallback_adapter.generate(
                prompt=prompt,
                model=model,
                system_prompt=system_prompt,
                temperature=temperature,
                max_tokens=max_tokens,
            )

        latency_ms = round((time.time() - start_time) * 1000, 2)
        response.request_id = request_id

        # Log AI Request to DB
        prompt_summary = prompt[:100] + "..." if len(prompt) > 100 else prompt
        req_log = AIRequestLogModel(
            user_id=user_id,
            request_id=request_id,
            provider=response.provider,
            model=response.model,
            prompt_summary=prompt_summary,
            status=status_str,
            latency_ms=latency_ms,
        )
        db.add(req_log)

        # Log AI Token Usage to DB
        usage_log = AIUsageModel(
            user_id=user_id,
            request_id=request_id,
            provider=response.provider,
            model=response.model,
            prompt_tokens=response.usage.prompt_tokens,
            completion_tokens=response.usage.completion_tokens,
            total_tokens=response.usage.total_tokens,
            cost_usd=response.usage.estimated_cost_usd,
        )
        db.add(usage_log)

        await db.commit()
        return response

    async def stream_response(
        self,
        prompt: str,
        user_id: str,
        db: AsyncSession,
        provider: str = "local",
        model: str = "flowpilot-local-v1",
        system_prompt: Optional[str] = None,
    ) -> AsyncGenerator[str, None]:
        self.validate_ai_policy(prompt)
        target_provider = self.get_provider(provider)

        async for chunk in target_provider.stream(prompt=prompt, model=model, system_prompt=system_prompt):
            yield chunk

    async def structured_output(
        self,
        prompt: str,
        response_schema: Dict[str, Any],
        user_id: str,
        db: AsyncSession,
        provider: str = "local",
        model: str = "flowpilot-local-v1",
    ) -> Dict[str, Any]:
        self.validate_ai_policy(prompt)
        target_provider = self.get_provider(provider)
        return await target_provider.structured_output(prompt, response_schema, model=model)


# Global AIService singleton
ai_service = AIService()
