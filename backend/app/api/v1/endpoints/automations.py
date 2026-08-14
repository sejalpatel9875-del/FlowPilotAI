from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import UserModel
from app.models.automation import AutomationModel, AutomationRunModel
from app.services.automation_service import AutomationService

router = APIRouter()


class CreateAutomationRequest(BaseModel):
    name: str = Field(..., description="Automation rule name")
    triggerType: str = Field(..., description="One of 10 triggers (e.g. NEW_LEAD, REPLY_RECEIVED, TASK_DUE)")
    actionType: str = Field(..., description="One of 7 actions (e.g. GENERATE_DRAFT, CREATE_TASK, UPDATE_LEAD)")
    description: Optional[str] = Field(None)
    conditionJson: Optional[str] = Field(None)
    aiDecisionPrompt: Optional[str] = Field(None)
    actionParamsJson: Optional[str] = Field(None)
    requiresApproval: bool = Field(default=True, description="Approval gatekeeper requirement")


class ToggleStatusRequest(BaseModel):
    status: str = Field(..., description="ACTIVE or PAUSED")


@router.get("")
async def list_automations_and_templates(
    user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List active user automations and pre-built templates."""
    res = await db.execute(
        select(AutomationModel)
        .options(selectinload(AutomationModel.runs))
        .where(AutomationModel.user_id == user.id)
    )
    user_automations = res.scalars().all()

    templates = AutomationService.get_prebuilt_templates()

    return {
        "templates": templates,
        "totalAutomations": len(user_automations),
        "automations": [
            {
                "id": a.id,
                "name": a.name,
                "description": a.description,
                "triggerType": a.trigger_type,
                "actionType": a.action_type,
                "requiresApproval": a.requires_approval,
                "status": a.status,
                "isActive": a.is_active,
                "aiDecisionPrompt": a.ai_decision_prompt,
                "runsCount": len(a.runs),
                "lastRun": a.runs[-1].executed_at.strftime("%Y-%m-%d %H:%M UTC") if a.runs else None
            }
            for a in user_automations
        ]
    }


@router.post("")
async def create_automation(
    req: CreateAutomationRequest,
    user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new automation workflow rule."""
    try:
        auto = await AutomationService.create_automation(
            name=req.name,
            trigger_type=req.triggerType,
            action_type=req.actionType,
            description=req.description,
            condition_json=req.conditionJson,
            ai_decision_prompt=req.aiDecisionPrompt,
            action_params_json=req.actionParamsJson,
            requires_approval=req.requiresApproval,
            user_id=user.id,
            db=db
        )
        return {
            "id": auto.id,
            "name": auto.name,
            "triggerType": auto.trigger_type,
            "actionType": auto.action_type,
            "status": auto.status,
            "message": "Automation workflow created successfully."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Automation creation failed: {str(e)}")


@router.get("/runs")
async def list_automation_runs(
    user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Retrieve execution runs and failure audit logs across user automations."""
    res = await db.execute(
        select(AutomationRunModel)
        .join(AutomationModel)
        .where(AutomationModel.user_id == user.id)
        .order_by(AutomationRunModel.executed_at.desc())
        .limit(50)
    )
    runs = res.scalars().all()

    return {
        "totalRuns": len(runs),
        "runs": [
            {
                "id": r.id,
                "automationId": r.automation_id,
                "triggerEvent": r.trigger_event,
                "status": r.status,
                "aiDecisionSummary": r.ai_decision_summary,
                "logs": r.logs,
                "errorMessage": r.error_message,
                "executedAt": r.executed_at.strftime("%Y-%m-%d %H:%M UTC")
            }
            for r in runs
        ]
    }


@router.post("/{automation_id}/test")
async def test_automation_execution(
    automation_id: str,
    user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Test execute an automation workflow manually."""
    try:
        run_res = await AutomationService.execute_automation_workflow(
            automation_id=automation_id,
            user_id=user.id,
            db=db,
            trigger_context={"event": "Manual Test Trigger"}
        )
        return run_res
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Automation test failed: {str(e)}")


@router.post("/{automation_id}/status")
async def toggle_automation_status(
    automation_id: str,
    req: ToggleStatusRequest,
    user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Pause or resume an automation rule."""
    try:
        auto = await AutomationService.toggle_status(automation_id, req.status, user.id, db)
        return {"id": auto.id, "status": auto.status, "isActive": auto.is_active}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
