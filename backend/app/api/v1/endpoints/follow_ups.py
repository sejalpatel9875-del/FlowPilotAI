from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import UserModel
from app.models.follow_up import FollowUpSequenceModel, FollowUpModel
from app.services.follow_up_service import FollowUpService, STOP_STAGES

router = APIRouter()


class StartSequenceRequest(BaseModel):
    leadId: str = Field(..., description="Target Lead ID")


@router.get("")
async def list_follow_ups(
    queue: Optional[str] = Query("due_today", description="due_today, upcoming, waiting, completed, or stopped"),
    user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List follow-up items organized by UI queues (due_today, upcoming, waiting, completed, stopped)."""
    now = datetime.utcnow()
    query = (
        select(FollowUpModel)
        .options(selectinload(FollowUpModel.sequence).selectinload(FollowUpSequenceModel.lead))
        .join(FollowUpSequenceModel)
        .where(FollowUpSequenceModel.user_id == user.id)
    )

    # Evaluate stop conditions across all active sequences
    seqs_res = await db.execute(select(FollowUpSequenceModel).where(FollowUpSequenceModel.user_id == user.id, FollowUpSequenceModel.status == "ACTIVE"))
    active_seqs = seqs_res.scalars().all()
    for seq in active_seqs:
        await FollowUpService.check_and_apply_stop_conditions(seq.lead_id, db)

    q = (queue or "due_today").lower()

    if q == "due_today":
        query = query.where(FollowUpModel.status.in_(["DUE", "UPCOMING"]), FollowUpModel.due_date <= now)
    elif q == "upcoming":
        query = query.where(FollowUpModel.status == "UPCOMING", FollowUpModel.due_date > now)
    elif q == "waiting":
        query = query.where(FollowUpModel.status == "WAITING")
    elif q == "completed":
        query = query.where(FollowUpModel.status == "COMPLETED")
    elif q == "stopped":
        query = query.where(FollowUpModel.status == "STOPPED")

    query = query.order_by(FollowUpModel.due_date.asc())
    res = await db.execute(query)
    items = res.scalars().all()

    return {
        "queue": q,
        "totalItems": len(items),
        "items": [
            {
                "id": item.id,
                "sequenceId": item.sequence_id,
                "leadId": item.sequence.lead_id if item.sequence else "",
                "company": item.sequence.lead.company if (item.sequence and item.sequence.lead) else "Unknown",
                "leadName": item.sequence.lead.name if (item.sequence and item.sequence.lead) else "Unknown",
                "leadEmail": item.sequence.lead.email if (item.sequence and item.sequence.lead) else "",
                "leadStatus": item.sequence.lead.status if (item.sequence and item.sequence.lead) else "New",
                "stepNumber": item.step_number,
                "delayDays": item.delay_days,
                "dueDate": item.due_date.strftime("%Y-%m-%d %H:%M UTC"),
                "status": item.status,
                "draftBody": item.draft_body,
                "aiReasoning": item.ai_reasoning,
                "sentAt": item.sent_at.strftime("%Y-%m-%d %H:%M UTC") if item.sent_at else None,
            }
            for item in items
        ]
    }


@router.post("/start")
async def start_followup_sequence(
    req: StartSequenceRequest,
    user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Start 3-step follow-up sequence for lead."""
    try:
        seq = await FollowUpService.start_sequence(req.leadId, user.id, db)
        return {
            "status": "success",
            "sequenceId": seq.id,
            "leadId": seq.lead_id,
            "message": "Initialized 3-step follow-up sequence (3d -> 7d -> 14d)."
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{followup_id}/explain")
async def explain_why_followup(
    followup_id: str,
    user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """AI Feature: Why should I follow up? Generates concise contextual reasoning."""
    try:
        explanation = await FollowUpService.explain_why_followup(followup_id, user.id, db)
        return {"followupId": followup_id, "aiReasoning": explanation}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{followup_id}/generate-draft")
async def generate_followup_draft(
    followup_id: str,
    user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Generate tailored AI follow-up email draft."""
    try:
        draft = await FollowUpService.generate_followup_draft(followup_id, user.id, db)
        return {"followupId": followup_id, "draftBody": draft}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{followup_id}/send")
async def send_followup(
    followup_id: str,
    user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Dispatch follow-up and advance/complete sequence."""
    res = await db.execute(
        select(FollowUpModel)
        .options(selectinload(FollowUpModel.sequence))
        .where(FollowUpModel.id == followup_id)
    )
    fu = res.scalar_one_or_none()
    if not fu or not fu.sequence:
        raise HTTPException(status_code=404, detail="Follow-up item not found.")

    fu.status = "COMPLETED"
    fu.sent_at = datetime.utcnow()

    # Advance sequence step
    if fu.step_number >= 3:
        fu.sequence.status = "COMPLETED"
    else:
        fu.sequence.current_step = fu.step_number + 1

    await db.commit()
    return {"status": "COMPLETED", "followupId": fu.id, "sentAt": fu.sent_at.strftime("%Y-%m-%d %H:%M UTC")}


@router.post("/{followup_id}/stop")
async def stop_followup_sequence(
    followup_id: str,
    user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Manually stop follow-up sequence."""
    res = await db.execute(
        select(FollowUpModel)
        .options(selectinload(FollowUpModel.sequence).selectinload(FollowUpSequenceModel.follow_ups))
        .where(FollowUpModel.id == followup_id)
    )
    fu = res.scalar_one_or_none()
    if not fu or not fu.sequence:
        raise HTTPException(status_code=404, detail="Follow-up item not found.")

    fu.sequence.status = "STOPPED"
    for item in fu.sequence.follow_ups:
        if item.status in ["DUE", "UPCOMING", "WAITING"]:
            item.status = "STOPPED"

    await db.commit()
    return {"status": "STOPPED", "sequenceId": fu.sequence_id}
