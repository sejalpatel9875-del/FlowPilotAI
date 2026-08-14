from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import UserModel
from app.models.governance import AuditLogModel
from app.services.security_guard_service import (
    PromptInjectionDetector,
    SensitiveDataFilter,
    SecurityControlEvaluator
)

router = APIRouter()


class ScanPromptRequest(BaseModel):
    queryText: str = Field(..., description="Prompt or text string to scan")


@router.get("/dashboard")
async def get_security_dashboard(
    user: UserModel = Depends(get_current_user)
):
    """Retrieve measurable security controls metrics across 7 domain dimensions."""
    controls = SecurityControlEvaluator.get_measurable_controls()
    return controls


@router.get("/events")
async def list_security_audit_events(
    limit: int = Query(50, ge=1, le=200),
    user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List audit security events and tool executions."""
    res = await db.execute(
        select(AuditLogModel)
        .order_by(AuditLogModel.created_at.desc())
        .limit(limit)
    )
    logs = res.scalars().all()

    return {
        "totalEvents": len(logs),
        "events": [
            {
                "id": log.id,
                "userId": log.user_id,
                "action": log.action,
                "resourceType": log.resource_type,
                "resourceId": log.resource_id,
                "ipAddress": log.ip_address,
                "details": log.details,
                "timestamp": log.created_at.strftime("%Y-%m-%d %H:%M:%S UTC")
            }
            for log in logs
        ]
    }


@router.post("/scan-prompt")
async def scan_prompt_for_injection_and_secrets(
    req: ScanPromptRequest,
    user: UserModel = Depends(get_current_user)
):
    """Test scanner for prompt injection vectors and sensitive data secret redaction."""
    injection_res = PromptInjectionDetector.detect_injection(req.queryText)
    redacted_text, redaction_count = SensitiveDataFilter.redact_sensitive_data(req.queryText)

    return {
        "promptInjectionScan": injection_res,
        "sensitiveDataScan": {
            "redactionsCount": redaction_count,
            "originalLength": len(req.queryText),
            "sanitizedOutput": redacted_text
        }
    }
