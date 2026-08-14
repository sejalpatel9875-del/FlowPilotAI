import uuid
import json
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import UserModel
from app.models.ai_request import AIRequestModel
from app.services.llm.base_provider import LLMRequest
from app.services.llm_service import LLMService

router = APIRouter()


class GenerateTextRequest(BaseModel):
    prompt: str = Field(..., description="User prompt text")
    systemPrompt: Optional[str] = Field(None, description="Optional system directive")
    provider: Optional[str] = Field(None, description="Target LLM provider (gemini, openai, ollama)")
    model: Optional[str] = Field(None, description="Target model name")
    temperature: float = Field(default=0.7, description="Generation temperature")
    maxTokens: Optional[int] = Field(default=1024, description="Max token output limit")


class StructuredTextRequest(BaseModel):
    prompt: str = Field(..., description="User prompt text")
    systemPrompt: Optional[str] = Field(None, description="Optional system directive")
    jsonSchema: Dict[str, Any] = Field(..., description="Target JSON schema specification")
    provider: Optional[str] = Field(None)
    model: Optional[str] = Field(None)


@router.post("/generate")
async def generate_ai_text(
    req: GenerateTextRequest,
    user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Synchronous AI generation endpoint."""
    llm_req = LLMRequest(
        prompt=req.prompt,
        system_prompt=req.systemPrompt,
        model=req.model,
        temperature=req.temperature,
        max_tokens=req.maxTokens
    )
    req_id = f"req_{uuid.uuid4().hex[:12]}"
    try:
        # Map legacy 'local' provider to ollama
        p_name = "ollama" if req.provider == "local" else req.provider
        res = await LLMService.generate(
            req=llm_req,
            user_id=user.id,
            db=db,
            provider_name=p_name
        )
        return {
            "requestId": req_id,
            "text": res.text,
            "provider": res.provider,
            "model": res.model,
            "usage": {
                "inputTokens": res.usage.input_tokens,
                "outputTokens": res.usage.output_tokens,
                "totalTokens": res.usage.total_tokens,
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI generation failed: {str(e)}")


@router.get("/providers")
async def list_ai_providers(
    user: UserModel = Depends(get_current_user)
):
    """List available LLM providers."""
    return {
        "providers": [
            {"id": "gemini", "name": "Google Gemini", "defaultModel": "gemini-1.5-flash", "status": "active"},
            {"id": "openai", "name": "OpenAI Compatible", "defaultModel": "gpt-4o", "status": "active"},
            {"id": "ollama", "name": "Local Ollama", "defaultModel": "llama3", "status": "active"},
        ]
    }


@router.post("/stream")
async def stream_ai_text(
    req: GenerateTextRequest,
    user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Server-Sent Events (SSE) streaming AI generation endpoint."""
    llm_req = LLMRequest(
        prompt=req.prompt,
        system_prompt=req.systemPrompt,
        model=req.model,
        temperature=req.temperature,
        max_tokens=req.maxTokens
    )
    p_name = "ollama" if req.provider == "local" else req.provider

    async def event_generator():
        try:
            async for token in LLMService.stream(
                req=llm_req,
                user_id=user.id,
                db=db,
                provider_name=p_name
            ):
                payload = json.dumps({"token": token})
                yield f"data: {payload}\n\n"
            yield "data: [DONE]\n\n"
        except Exception as e:
            err_payload = json.dumps({"error": str(e)})
            yield f"data: {err_payload}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.post("/structured")
async def structured_ai_output(
    req: StructuredTextRequest,
    user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Validated structured JSON schema output endpoint."""
    llm_req = LLMRequest(
        prompt=req.prompt,
        system_prompt=req.systemPrompt,
        model=req.model,
        json_schema=req.jsonSchema
    )
    p_name = "ollama" if req.provider == "local" else req.provider
    try:
        res = await LLMService.structured_output(
            req=llm_req,
            schema=req.jsonSchema,
            user_id=user.id,
            db=db,
            provider_name=p_name
        )
        try:
            parsed_json = json.loads(res.text)
        except Exception:
            parsed_json = {"raw": res.text}

        return {
            "structuredOutput": parsed_json,
            "provider": res.provider,
            "model": res.model,
            "usage": {
                "inputTokens": res.usage.input_tokens,
                "outputTokens": res.usage.output_tokens,
                "totalTokens": res.usage.total_tokens,
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Structured AI output failed: {str(e)}")


@router.get("/usage")
async def get_user_ai_usage(
    user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Retrieve authenticated user's LLM usage analytics and request history."""
    res = await db.execute(
        select(AIRequestModel)
        .where(AIRequestModel.user_id == user.id)
        .order_by(AIRequestModel.created_at.desc())
        .limit(50)
    )
    requests = res.scalars().all()

    total_tokens = sum(r.total_tokens or 0 for r in requests)
    avg_latency = (sum(r.latency_ms for r in requests) / len(requests)) if requests else 0.0

    return {
        "totalRequests": len(requests),
        "totalTokens": total_tokens,
        "summaryMetrics": {
            "totalRequests": len(requests),
            "totalTokensConsumed": total_tokens,
            "avgLatencyMs": round(avg_latency, 1),
        },
        "recentRequests": [
            {
                "id": r.id,
                "provider": r.provider,
                "model": r.model,
                "requestType": r.request_type,
                "totalTokens": r.total_tokens,
                "latencyMs": round(r.latency_ms, 1),
                "status": r.status,
                "createdAt": r.created_at.strftime("%Y-%m-%d %H:%M:%S UTC"),
            }
            for r in requests
        ]
    }
