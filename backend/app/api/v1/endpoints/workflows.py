import json
import asyncio
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import UserModel
from app.models.workflow import (
    WorkflowModel,
    WorkflowStepModel,
    WorkflowApprovalModel,
    WorkflowEventModel,
)
from app.services.workflow.workflow_engine import WorkflowExecutionEngine

router = APIRouter()


class CreateWorkflowRequest(BaseModel):
    goal: str = Field(..., min_length=3, description="High-level natural language objective to orchestrate")


class ApprovalDecisionRequest(BaseModel):
    approvalId: str = Field(..., description="ID of the pending approval record")
    decision: str = Field(..., description="'approved' or 'rejected'")
    reason: Optional[str] = Field(None, description="Optional explanation for approval or rejection")


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_workflow(
    req: CreateWorkflowRequest,
    user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Decomposes, validates, and initiates a multi-agent workflow."""
    try:
        wf = await WorkflowExecutionEngine.create_and_start_workflow(
            user_id=user.id,
            goal=req.goal,
            db=db
        )
        return {
            "id": wf.id,
            "title": wf.title,
            "goal": wf.goal,
            "status": wf.status,
            "totalSteps": wf.total_steps,
            "completedSteps": wf.completed_steps,
            "replanCount": wf.replan_count,
            "startedAt": wf.started_at.isoformat() if wf.started_at else None,
            "completedAt": wf.completed_at.isoformat() if wf.completed_at else None,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Workflow execution failed: {str(e)}")


@router.get("")
async def list_workflows(
    status_filter: Optional[str] = Query(None, alias="status"),
    user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Lists workflows belonging strictly to the authenticated user."""
    query = select(WorkflowModel).where(WorkflowModel.user_id == user.id, WorkflowModel.is_deleted == False)
    if status_filter:
        query = query.where(WorkflowModel.status == status_filter)
    
    query = query.order_by(WorkflowModel.created_at.desc())
    res = await db.execute(query)
    workflows = res.scalars().all()

    return {
        "workflows": [
            {
                "id": w.id,
                "title": w.title,
                "goal": w.goal,
                "status": w.status,
                "totalSteps": w.total_steps,
                "completedSteps": w.completed_steps,
                "createdAt": w.created_at.isoformat() if w.created_at else None,
                "completedAt": w.completed_at.isoformat() if w.completed_at else None,
            }
            for w in workflows
        ]
    }


@router.get("/{workflow_id}")
async def get_workflow(
    workflow_id: str,
    user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Retrieves full workflow state, execution steps, and pending approval records."""
    res_wf = await db.execute(
        select(WorkflowModel).where(
            WorkflowModel.id == workflow_id,
            WorkflowModel.user_id == user.id,
            WorkflowModel.is_deleted == False
        )
    )
    wf = res_wf.scalar_one_or_none()
    if not wf:
        raise HTTPException(status_code=404, detail="Workflow not found or access denied.")

    # Load steps
    res_steps = await db.execute(
        select(WorkflowStepModel)
        .where(WorkflowStepModel.workflow_id == workflow_id, WorkflowStepModel.user_id == user.id)
        .order_by(WorkflowStepModel.step_order)
    )
    steps = res_steps.scalars().all()

    # Load pending approvals
    res_app = await db.execute(
        select(WorkflowApprovalModel)
        .where(
            WorkflowApprovalModel.workflow_id == workflow_id,
            WorkflowApprovalModel.user_id == user.id,
            WorkflowApprovalModel.status == "pending"
        )
    )
    approvals = res_app.scalars().all()

    return {
        "id": wf.id,
        "title": wf.title,
        "goal": wf.goal,
        "status": wf.status,
        "totalSteps": wf.total_steps,
        "completedSteps": wf.completed_steps,
        "replanCount": wf.replan_count,
        "errorMessage": wf.error_message,
        "startedAt": wf.started_at.isoformat() if wf.started_at else None,
        "completedAt": wf.completed_at.isoformat() if wf.completed_at else None,
        "steps": [
            {
                "id": s.id,
                "stepKey": s.step_key,
                "order": s.step_order,
                "agent": s.agent_name,
                "action": s.action,
                "description": s.description,
                "dependsOn": json.loads(s.depends_on_json or "[]"),
                "requiresApproval": s.requires_approval,
                "status": s.status,
                "output": json.loads(s.output_data_json or "{}") if s.output_data_json else None,
                "latencyMs": s.latency_ms,
                "errorInfo": s.error_info,
            }
            for s in steps
        ],
        "pendingApprovals": [
            {
                "id": a.id,
                "stepKey": a.step_key,
                "proposedAction": a.proposed_action,
                "status": a.status,
                "createdAt": a.created_at.isoformat() if a.created_at else None,
            }
            for a in approvals
        ]
    }


@router.post("/{workflow_id}/approve")
async def approve_workflow_action(
    workflow_id: str,
    req: ApprovalDecisionRequest,
    user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Grants human approval for a paused workflow side effect and resumes execution."""
    try:
        wf = await WorkflowExecutionEngine.process_approval(
            workflow_id=workflow_id,
            approval_id=req.approvalId,
            decision="approved",
            user_id=user.id,
            reason=req.reason,
            db=db
        )
        return {
            "workflowId": wf.id,
            "status": wf.status,
            "completedSteps": wf.completed_steps,
            "totalSteps": wf.total_steps,
            "message": "Approval granted. Execution resumed."
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process approval: {str(e)}")


@router.post("/{workflow_id}/reject")
async def reject_workflow_action(
    workflow_id: str,
    req: ApprovalDecisionRequest,
    user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Rejects a proposed workflow side effect and safely terminates the workflow."""
    try:
        wf = await WorkflowExecutionEngine.process_approval(
            workflow_id=workflow_id,
            approval_id=req.approvalId,
            decision="rejected",
            user_id=user.id,
            reason=req.reason,
            db=db
        )
        return {
            "workflowId": wf.id,
            "status": wf.status,
            "completedSteps": wf.completed_steps,
            "totalSteps": wf.total_steps,
            "message": "Action rejected by user. Workflow terminated safely."
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process rejection: {str(e)}")


@router.post("/{workflow_id}/cancel")
async def cancel_workflow(
    workflow_id: str,
    user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Cancels a running or waiting workflow."""
    try:
        wf = await WorkflowExecutionEngine.cancel_workflow(
            workflow_id=workflow_id,
            user_id=user.id,
            db=db
        )
        return {
            "workflowId": wf.id,
            "status": wf.status,
            "message": "Workflow successfully cancelled."
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to cancel workflow: {str(e)}")


@router.get("/{workflow_id}/events")
async def get_workflow_events(
    workflow_id: str,
    user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Retrieves the immutable audit trail of events for a workflow."""
    # Verify workflow ownership
    res_wf = await db.execute(
        select(WorkflowModel).where(WorkflowModel.id == workflow_id, WorkflowModel.user_id == user.id)
    )
    if not res_wf.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Workflow not found or access denied.")

    res_events = await db.execute(
        select(WorkflowEventModel)
        .where(WorkflowEventModel.workflow_id == workflow_id, WorkflowEventModel.user_id == user.id)
        .order_by(WorkflowEventModel.timestamp.asc())
    )
    events = res_events.scalars().all()

    return {
        "workflowId": workflow_id,
        "events": [
            {
                "id": ev.id,
                "eventType": ev.event_type,
                "stepKey": ev.step_key,
                "details": json.loads(ev.details_json or "{}"),
                "timestamp": ev.timestamp.isoformat(),
            }
            for ev in events
        ]
    }


@router.get("/{workflow_id}/stream")
async def stream_workflow(
    workflow_id: str,
    user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Streams live workflow execution state changes and events over Server-Sent Events (SSE)."""
    # 1. Verify tenant ownership
    res_wf = await db.execute(
        select(WorkflowModel).where(
            WorkflowModel.id == workflow_id,
            WorkflowModel.user_id == user.id,
            WorkflowModel.is_deleted == False
        )
    )
    wf = res_wf.scalar_one_or_none()
    if not wf:
        raise HTTPException(status_code=404, detail="Workflow not found or access denied.")

    async def event_generator():
        # Yield initial connected event
        yield f"event: connected\ndata: {json.dumps({'workflowId': workflow_id, 'status': wf.status, 'totalSteps': wf.total_steps, 'completedSteps': wf.completed_steps})}\n\n"

        last_status = wf.status
        last_completed = wf.completed_steps

        # Stream updates until workflow terminal state or approval gate
        for _ in range(30):  # Maximum 30 iterations / safety timeout
            await asyncio.sleep(0.5)
            
            # Query fresh state
            res = await db.execute(
                select(WorkflowModel).where(WorkflowModel.id == workflow_id, WorkflowModel.user_id == user.id)
            )
            current_wf = res.scalar_one_or_none()
            if not current_wf:
                break

            if current_wf.status != last_status or current_wf.completed_steps != last_completed:
                last_status = current_wf.status
                last_completed = current_wf.completed_steps
                yield f"event: state_change\ndata: {json.dumps({'workflowId': workflow_id, 'status': current_wf.status, 'totalSteps': current_wf.total_steps, 'completedSteps': current_wf.completed_steps})}\n\n"

            if current_wf.status in ("COMPLETED", "WAITING_FOR_APPROVAL", "FAILED", "REJECTED", "CANCELLED"):
                yield f"event: terminal\ndata: {json.dumps({'workflowId': workflow_id, 'status': current_wf.status, 'completedSteps': current_wf.completed_steps})}\n\n"
                break
            else:
                yield f"event: ping\ndata: {json.dumps({'timestamp': asyncio.get_event_loop().time()})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )

