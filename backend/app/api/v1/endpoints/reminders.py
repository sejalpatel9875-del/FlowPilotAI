from datetime import datetime, timedelta
from typing import Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.core.database import get_db
from app.api.v1.endpoints.auth import get_current_user
from app.models.user import UserModel
from app.services.reminder_service import ReminderService

router = APIRouter()


class ReminderCreate(BaseModel):
    title: str
    remind_at: datetime
    description: Optional[str] = None
    priority: str = "medium"
    linked_lead_id: Optional[str] = None
    linked_project_id: Optional[str] = None
    recurrence: Optional[str] = None


class ReminderUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    remind_at: Optional[datetime] = None
    priority: Optional[str] = None
    recurrence: Optional[str] = None


class SnoozeRequest(BaseModel):
    snooze_minutes: Optional[int] = None
    snooze_until: Optional[datetime] = None


class SmartSuggestRequest(BaseModel):
    prompt: str


@router.get("")
async def list_reminders(
    status_filter: Optional[str] = Query(None, alias="status"),
    user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """List reminders with optional filter (due_today, upcoming, completed, snoozed, active)."""
    reminders = await ReminderService.list_reminders(user.id, status_filter or "active", db)
    return {
        "reminders": [
            {
                "id": r.id,
                "title": r.title,
                "description": r.description,
                "remind_at": r.remind_at,
                "status": r.status,
                "priority": r.priority,
                "recurrence": r.recurrence,
                "snoozed_until": r.snoozed_until,
                "linked_lead_id": r.linked_lead_id,
                "linked_project_id": r.linked_project_id,
                "created_at": r.created_at
            }
            for r in reminders
        ]
    }


@router.get("/due")
async def get_due_reminders(
    user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Get due/overdue reminders."""
    reminders = await ReminderService.get_due_reminders(user.id, db)
    return {
        "due_reminders": [
            {
                "id": r.id,
                "title": r.title,
                "remind_at": r.remind_at,
                "priority": r.priority,
                "linked_lead_id": r.linked_lead_id,
                "linked_project_id": r.linked_project_id
            }
            for r in reminders
        ],
        "count": len(reminders)
    }


@router.post("")
async def create_reminder(
    req: ReminderCreate,
    user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Create a new reminder."""
    reminder = await ReminderService.create_reminder(
        user_id=user.id,
        title=req.title,
        remind_at=req.remind_at,
        db=db,
        description=req.description,
        priority=req.priority,
        linked_lead_id=req.linked_lead_id,
        linked_project_id=req.linked_project_id,
        recurrence=req.recurrence
    )
    return {"id": reminder.id, "status": "created"}


@router.post("/smart-suggest")
async def smart_suggest_reminders(
    req: SmartSuggestRequest,
    user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """AI-suggest reminders based on pipeline state."""
    result = await ReminderService.generate_smart_reminders(user.id, req.prompt, db)
    return result


@router.get("/{reminder_id}")
async def get_reminder(
    reminder_id: str,
    user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Get a single reminder by ID."""
    try:
        r = await ReminderService.get_reminder(user.id, reminder_id, db)
        return {
            "id": r.id,
            "title": r.title,
            "description": r.description,
            "remind_at": r.remind_at,
            "status": r.status,
            "priority": r.priority,
            "recurrence": r.recurrence,
            "snoozed_until": r.snoozed_until,
            "linked_lead_id": r.linked_lead_id,
            "linked_project_id": r.linked_project_id,
            "created_at": r.created_at
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.patch("/{reminder_id}")
async def update_reminder(
    reminder_id: str,
    req: ReminderUpdate,
    user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Update a reminder."""
    try:
        reminder = await ReminderService.get_reminder(user.id, reminder_id, db)
        updates = req.model_dump(exclude_unset=True)
        for key, value in updates.items():
            if hasattr(reminder, key):
                setattr(reminder, key, value)
        await db.commit()
        await db.refresh(reminder)
        return {"id": reminder.id, "status": "updated"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{reminder_id}/snooze")
async def snooze_reminder(
    reminder_id: str,
    req: SnoozeRequest,
    user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Snooze a reminder."""
    snooze_until = req.snooze_until
    if not snooze_until and req.snooze_minutes:
        snooze_until = datetime.utcnow() + timedelta(minutes=req.snooze_minutes)
    if not snooze_until:
        raise HTTPException(status_code=400, detail="Provide snooze_minutes or snooze_until")
    try:
        reminder = await ReminderService.snooze_reminder(user.id, reminder_id, snooze_until, db)
        return {"id": reminder.id, "status": "snoozed", "snoozed_until": reminder.snoozed_until}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{reminder_id}/complete")
async def complete_reminder(
    reminder_id: str,
    user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Mark a reminder as completed."""
    try:
        reminder = await ReminderService.complete_reminder(user.id, reminder_id, db)
        return {"id": reminder.id, "status": "completed"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/{reminder_id}")
async def dismiss_reminder(
    reminder_id: str,
    user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Dismiss/delete a reminder."""
    try:
        reminder = await ReminderService.dismiss_reminder(user.id, reminder_id, db)
        return {"id": reminder.id, "status": "dismissed"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
