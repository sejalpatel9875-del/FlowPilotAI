from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import UserModel
from app.models.time_management import TimeBlockModel, UserTimePreferenceModel
from app.services.time_management_service import TimeManagementService

router = APIRouter()


class QuickPlanRequest(BaseModel):
    minutes: int = Field(default=60, description="Available minutes budget (e.g. 60)")


class TimeBlockActionRequest(BaseModel):
    action: str = Field(..., description="COMPLETE, SKIP, RESCHEDULE, SPLIT, or REDUCE_SCOPE")


@router.get("/schedule")
async def get_schedule(
    view: Optional[str] = Query("today", description="today or week"),
    user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Retrieve schedule timeblocks for today or week."""
    now = datetime.utcnow()
    query = (
        select(TimeBlockModel)
        .options(selectinload(TimeBlockModel.task))
        .where(TimeBlockModel.user_id == user.id)
    )

    if view == "today":
        start_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end_day = start_day + timedelta(days=1)
        query = query.where(TimeBlockModel.start_time >= start_day, TimeBlockModel.start_time < end_day)
    else:
        start_week = now - timedelta(days=now.weekday())
        end_week = start_week + timedelta(days=7)
        query = query.where(TimeBlockModel.start_time >= start_week, TimeBlockModel.start_time < end_week)

    query = query.order_by(TimeBlockModel.start_time.asc())
    res = await db.execute(query)
    blocks = res.scalars().all()

    return {
        "view": view,
        "totalBlocks": len(blocks),
        "topPriorities": [
            "1. Deliver High-Revenue Client Feature Architecture",
            "2. Conduct Deep Research on Client Pain Points",
            "3. Dedicated AI Agent Skill Mastery Session"
        ],
        "timeBlocks": [
            {
                "id": b.id,
                "title": b.title,
                "blockType": b.block_type,
                "startTime": b.start_time.strftime("%H:%M UTC"),
                "endTime": b.end_time.strftime("%H:%M UTC"),
                "status": b.status,
                "taskId": b.task_id,
            }
            for b in blocks
        ]
    }


@router.post("/plan-day")
async def trigger_ai_daily_planner(
    user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Trigger AI Daily Planner to generate Top 3 Priorities, Focus Blocks, Learning Block, and Breaks."""
    try:
        plan = await TimeManagementService.generate_daily_plan(user.id, db)
        return plan
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Daily planner execution failed: {str(e)}")


@router.post("/quick-plan")
async def trigger_quick_budget_plan(
    req: QuickPlanRequest,
    user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Feature: 'I only have X minutes' (e.g. 60 minutes). Creates highest-leverage schedule for time budget."""
    try:
        plan = await TimeManagementService.quick_time_budget_plan(user.id, req.minutes, db)
        return plan
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Quick plan execution failed: {str(e)}")


@router.post("/recalculate-missed")
async def trigger_recalculate_missed_tasks(
    user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Intelligently recalculate schedule for missed tasks (splits, scope reduction, rescheduling)."""
    try:
        res = await TimeManagementService.recalculate_missed_tasks(user.id, db)
        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Schedule recalculation failed: {str(e)}")


@router.post("/blocks/{block_id}/action")
async def apply_timeblock_action(
    block_id: str,
    req: TimeBlockActionRequest,
    user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Apply action (COMPLETE, SKIP, RESCHEDULE, SPLIT, REDUCE_SCOPE) on a timeblock."""
    res = await db.execute(
        select(TimeBlockModel).where(
            TimeBlockModel.id == block_id,
            TimeBlockModel.user_id == user.id
        )
    )
    tb = res.scalar_one_or_none()
    if not tb:
        raise HTTPException(status_code=404, detail="TimeBlock not found.")

    act = req.action.upper().strip()

    if act == "COMPLETE":
        tb.status = "COMPLETED"
    elif act == "SKIP":
        tb.status = "SKIPPED"
    elif act == "RESCHEDULE":
        tb.status = "RESCHEDULED"
        tb.start_time = tb.start_time + timedelta(days=1)
        tb.end_time = tb.end_time + timedelta(days=1)
    elif act == "SPLIT":
        tb.title = f"[Split Sprint 1] {tb.title}"
        tb.end_time = tb.start_time + timedelta(minutes=25)
    elif act in ["REDUCE_SCOPE", "REDUCE"]:
        tb.title = f"[Reduced Scope] {tb.title}"
        tb.status = "REDUCED_SCOPE"
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported action '{req.action}'. Allowed: COMPLETE, SKIP, RESCHEDULE, SPLIT, REDUCE_SCOPE.")

    await db.commit()
    await db.refresh(tb)

    return {"status": tb.status, "blockId": tb.id, "title": tb.title, "actionApplied": act}
