from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import UserModel
from app.models.outreach import OutreachMessageModel
from app.services.outreach_service import OutreachService, VALID_CHANNELS, VALID_STATUSES

router = APIRouter()


class GenerateOutreachRequest(BaseModel):
    leadId: str = Field(..., description="Target Lead ID")
    channel: str = Field(..., description="Email, LinkedIn connection note, Freelance proposal, or Contact form draft")
    customInstructions: Optional[str] = Field(None, description="Optional custom guidelines for OutreachAgent")


class EditOutreachRequest(BaseModel):
    subject: Optional[str] = None
    draftBody: Optional[str] = None


class ScheduleOutreachRequest(BaseModel):
    scheduledTime: Optional[str] = Field(None, description="ISO datetime string for scheduled delivery")


@router.get("")
async def list_outreach_messages(
    status_filter: Optional[str] = Query(None, alias="status"),
    channel_filter: Optional[str] = Query(None, alias="channel"),
    user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List outreach messages with status and channel filtering."""
    query = select(OutreachMessageModel).where(OutreachMessageModel.user_id == user.id)

    if status_filter:
        query = query.where(OutreachMessageModel.status == status_filter)

    if channel_filter:
        query = query.where(OutreachMessageModel.channel == channel_filter)

    query = query.order_by(OutreachMessageModel.created_at.desc())
    res = await db.execute(query)
    messages = res.scalars().all()

    return {
        "channels": VALID_CHANNELS,
        "statuses": VALID_STATUSES,
        "totalMessages": len(messages),
        "messages": [
            {
                "id": m.id,
                "leadId": m.lead_id,
                "leadCompany": m.lead.company if m.lead else "Unknown",
                "leadName": m.lead.name if m.lead else "Unknown",
                "leadEmail": m.lead.email if m.lead else "",
                "channel": m.channel,
                "subject": m.subject,
                "draftBody": m.draft_body,
                "status": m.status,
                "scheduledAt": m.scheduled_at.strftime("%Y-%m-%d %H:%M:%S UTC") if m.scheduled_at else None,
                "approvedAt": m.approved_at.strftime("%Y-%m-%d %H:%M:%S UTC") if m.approved_at else None,
                "sentAt": m.sent_at.strftime("%Y-%m-%d %H:%M:%S UTC") if m.sent_at else None,
                "createdAt": m.created_at.strftime("%Y-%m-%d %H:%M:%S UTC"),
            }
            for m in messages
        ]
    }


@router.post("/generate")
async def generate_outreach_message(
    req: GenerateOutreachRequest,
    user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Generate personalized outreach draft using OutreachAgent."""
    try:
        msg = await OutreachService.generate_draft(
            lead_id=req.leadId,
            channel=req.channel,
            user_id=user.id,
            db=db,
            custom_instructions=req.customInstructions
        )
        return {
            "id": msg.id,
            "channel": msg.channel,
            "subject": msg.subject,
            "draftBody": msg.draft_body,
            "status": msg.status,
            "message": "Outreach draft generated and placed in Human Approval Inbox."
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Outreach generation failed: {str(e)}")


@router.patch("/{message_id}")
async def edit_outreach_draft(
    message_id: str,
    req: EditOutreachRequest,
    user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Edit draft text or subject before approval."""
    res = await db.execute(
        select(OutreachMessageModel).where(
            OutreachMessageModel.id == message_id,
            OutreachMessageModel.user_id == user.id
        )
    )
    msg = res.scalar_one_or_none()
    if not msg:
        raise HTTPException(status_code=404, detail="Outreach message not found.")

    if req.subject is not None:
        msg.subject = req.subject
    if req.draftBody is not None:
        msg.draft_body = req.draftBody

    await db.commit()
    await db.refresh(msg)
    return {"status": "success", "id": msg.id, "subject": msg.subject, "draftBody": msg.draft_body}


@router.post("/{message_id}/approve")
async def approve_outreach_message(
    message_id: str,
    user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Approve outreach message in Human Approval Inbox."""
    try:
        msg = await OutreachService.update_status(message_id, "APPROVED", user.id, db)
        return {"status": "APPROVED", "id": msg.id, "approvedAt": msg.approved_at.strftime("%Y-%m-%d %H:%M:%S UTC")}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{message_id}/reject")
async def reject_outreach_message(
    message_id: str,
    user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Reject / Cancel outreach message."""
    try:
        msg = await OutreachService.update_status(message_id, "CANCELLED", user.id, db)
        return {"status": "CANCELLED", "id": msg.id}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{message_id}/schedule")
async def schedule_outreach_message(
    message_id: str,
    req: ScheduleOutreachRequest,
    user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Schedule outreach message delivery."""
    sched_dt = datetime.fromisoformat(req.scheduledTime) if req.scheduledTime else datetime.utcnow()
    try:
        msg = await OutreachService.update_status(message_id, "SCHEDULED", user.id, db, scheduled_time=sched_dt)
        return {"status": "SCHEDULED", "id": msg.id, "scheduledAt": msg.scheduled_at.strftime("%Y-%m-%d %H:%M:%S UTC")}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{message_id}/send")
async def send_outreach_message(
    message_id: str,
    user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Dispatch approved outreach message and update lead pipeline status."""
    try:
        msg = await OutreachService.update_status(message_id, "SENT", user.id, db)
        return {"status": "SENT", "id": msg.id, "sentAt": msg.sent_at.strftime("%Y-%m-%d %H:%M:%S UTC")}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
