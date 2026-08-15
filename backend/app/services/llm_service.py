import json
import time
import asyncio
import logging
from typing import Dict, Any, Optional, List, AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.ai_request import AIRequestModel
from app.services.security_guard_service import SensitiveDataFilter, PromptInjectionDetector
from app.services.llm.base_provider import LLMRequest, LLMResponse, LLMUsage, LLMProvider
from app.services.llm.provider_registry import llm_provider_registry

logger = logging.getLogger("flowpilot.llm_service")


class LLMService:
    @staticmethod
    async def _execute_with_retry(
        provider: LLMProvider,
        req: LLMRequest,
        max_retries: int = 3
    ) -> LLMResponse:
        """Executes LLM request with exponential backoff retries."""
        last_exception = None
        for attempt in range(max_retries):
            try:
                return await provider.generate(req)
            except Exception as e:
                last_exception = e
                logger.warning(f"LLM Attempt {attempt + 1}/{max_retries} failed for provider '{provider.provider_name}': {str(e)}")
                if attempt < max_retries - 1:
                    backoff = 0.5 * (2 ** attempt)
                    await asyncio.sleep(backoff)

        raise RuntimeError(f"LLM execution failed after {max_retries} attempts: {str(last_exception)}")

    @classmethod
    async def generate(
        cls,
        req: LLMRequest,
        user_id: str,
        db: AsyncSession,
        provider_name: Optional[str] = None
    ) -> LLMResponse:
        """Complete generation pipeline with prompt sanitization, retries, fallback, and usage logging."""
        start_time = time.time()
        target_provider_name = provider_name or settings.LLM_PROVIDER or "gemini"
        
        # 1. Input Validation & Sensitive Data Filtering
        clean_prompt, _ = SensitiveDataFilter.redact_sensitive_data(req.prompt)
        req.prompt = clean_prompt
        if req.system_prompt:
            clean_sys, _ = SensitiveDataFilter.redact_sensitive_data(req.system_prompt)
            req.system_prompt = clean_sys

        # 2. Select Provider
        provider = llm_provider_registry.get_provider(target_provider_name)
        status = "completed"
        error_code = None

        try:
            res = await cls._execute_with_retry(provider, req, max_retries=settings.LLM_MAX_RETRIES)
        except Exception as e:
            # Check Fallback Provider
            if settings.LLM_FALLBACK_ENABLED and settings.LLM_FALLBACK_PROVIDER:
                logger.info(f"Primary LLM provider '{target_provider_name}' failed. Attempting fallback provider '{settings.LLM_FALLBACK_PROVIDER}'...")
                try:
                    fallback_provider = llm_provider_registry.get_provider(settings.LLM_FALLBACK_PROVIDER)
                    if settings.LLM_FALLBACK_MODEL:
                        req.model = settings.LLM_FALLBACK_MODEL
                    res = await cls._execute_with_retry(fallback_provider, req, max_retries=2)
                except Exception as fb_err:
                    status = "failed"
                    error_code = str(fb_err)[:100]
                    raise RuntimeError(f"Both primary '{target_provider_name}' and fallback '{settings.LLM_FALLBACK_PROVIDER}' failed: {str(fb_err)}")
            else:
                status = "failed"
                error_code = str(e)[:100]
                raise e

        latency_ms = round((time.time() - start_time) * 1000, 2)

        # 3. Output Validation & Secret Masking
        res.text, _ = SensitiveDataFilter.redact_sensitive_data(res.text)

        # 4. Usage Tracking DB Persistence (`ai_requests`)
        try:
            ai_req = AIRequestModel(
                user_id=user_id,
                provider=res.provider,
                model=res.model,
                request_type="generate",
                input_tokens=res.usage.input_tokens,
                output_tokens=res.usage.output_tokens,
                total_tokens=res.usage.total_tokens,
                latency_ms=latency_ms,
                status=status,
                error_code=error_code
            )
            db.add(ai_req)
            await db.commit()
        except Exception as db_err:
            try:
                await db.rollback()
            except Exception:
                pass
            logger.warning(f"Failed to persist AI usage request log to database: {str(db_err)}")

        return res

    @classmethod
    async def stream(
        cls,
        req: LLMRequest,
        user_id: str,
        db: AsyncSession,
        provider_name: Optional[str] = None
    ) -> AsyncGenerator[str, None]:
        """Streaming token pipeline."""
        start_time = time.time()
        target_provider_name = provider_name or settings.LLM_PROVIDER or "gemini"
        
        clean_prompt, _ = SensitiveDataFilter.redact_sensitive_data(req.prompt)
        req.prompt = clean_prompt
        provider = llm_provider_registry.get_provider(target_provider_name)

        tokens_generated = 0
        async for chunk in provider.stream(req):
            tokens_generated += 1
            yield chunk

        latency_ms = round((time.time() - start_time) * 1000, 2)
        try:
            ai_req = AIRequestModel(
                user_id=user_id,
                provider=provider.provider_name,
                model=req.model or provider.default_model,
                request_type="stream",
                input_tokens=len(req.prompt) // 4,
                output_tokens=tokens_generated,
                total_tokens=(len(req.prompt) // 4) + tokens_generated,
                latency_ms=latency_ms,
                status="completed"
            )
            db.add(ai_req)
            await db.commit()
        except Exception as db_err:
            try:
                await db.rollback()
            except Exception:
                pass
            logger.warning(f"Failed to persist AI usage stream log to database: {str(db_err)}")



    @classmethod
    async def structured_output(
        cls,
        req: LLMRequest,
        schema: Dict[str, Any],
        user_id: str,
        db: AsyncSession,
        provider_name: Optional[str] = None
    ) -> LLMResponse:
        """Structured JSON schema output with JSON validation."""
        res = await cls.generate(req, user_id=user_id, db=db, provider_name=provider_name)
        try:
            # Validate JSON format
            json.loads(res.text)
        except json.JSONDecodeError:
            # Clean non-JSON wrappers if model added markdown ```json ... ```
            cleaned = res.text.strip()
            if cleaned.startswith("```json"):
                cleaned = cleaned[7:]
            if cleaned.startswith("```"):
                cleaned = cleaned[3:]
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]
            res.text = cleaned.strip()

        return res

    @classmethod
    async def embed(cls, text: str, provider_name: Optional[str] = None) -> List[float]:
        """Generate vector embedding."""
        target = provider_name or settings.LLM_PROVIDER or "gemini"
        provider = llm_provider_registry.get_provider(target)
        return await provider.embed(text)
