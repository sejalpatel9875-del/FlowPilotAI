from datetime import datetime
from typing import List, Optional, Any, Dict
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.api.v1.endpoints.auth import get_current_user
from app.models.user import UserModel
from app.services.invitation_service import InvitationService

router = APIRouter()

class CreateInvitationRequest(BaseModel):
    title: str
    recipient_name: str
    recipient_email: str
    invitation_type: str = "meeting"
    description: Optional[str] = None
    scheduled_at: Optional[datetime] = None
    location: Optional[str] = None
    meeting_link: Optional[str] = None

class GenerateInvitationRequest(BaseModel):
    leadId: str
    invitationType: str
    prompt: str

class EditInvitationRequest(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    scheduled_at: Optional[datetime] = None
    location: Optional[str] = None
    meeting_link: Optional[str] = None
    message_body: Optional[str] = None

@router.get("")
async def list_invitations(
    status_filter: Optional[str] = Query(None, alias="status"),
    user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    invitations = await InvitationService.list_invitations(user.id, status_filter, db)
    return {
        "invitations": [
            {
                "id": i.id,
                "title": i.title,
                "recipient_name": i.recipient_name,
                "recipient_email": i.recipient_email,
                "invitation_type": i.invitation_type,
                "status": i.status,
                "scheduled_at": i.scheduled_at,
                "created_at": i.created_at
            }
            for i in invitations
        ]
    }

@router.post("")
async def create_invitation(
    req: CreateInvitationRequest,
    user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    invitation = await InvitationService.create_invitation(
        user_id=user.id,
        title=req.title,
        recipient_name=req.recipient_name,
        recipient_email=req.recipient_email,
        invitation_type=req.invitation_type,
        description=req.description,
        scheduled_at=req.scheduled_at,
        location=req.location,
        meeting_link=req.meeting_link,
        db=db
    )
    return {"id": invitation.id, "status": "created"}

@router.post("/generate")
async def generate_invitation(
    req: GenerateInvitationRequest,
    user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    try:
        invitation = await InvitationService.generate_ai_invitation(
            user_id=user.id,
            lead_id=req.leadId,
            invitation_type=req.invitationType,
            prompt=req.prompt,
            db=db
        )
        return {"id": invitation.id, "status": "generated"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{invitation_id}")
async def get_invitation(
    invitation_id: str,
    user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    try:
        inv = await InvitationService.get_invitation(user.id, invitation_id, db)
        return {
            "id": inv.id,
            "title": inv.title,
            "recipient_name": inv.recipient_name,
            "recipient_email": inv.recipient_email,
            "invitation_type": inv.invitation_type,
            "description": inv.description,
            "scheduled_at": inv.scheduled_at,
            "location": inv.location,
            "meeting_link": inv.meeting_link,
            "message_body": inv.message_body,
            "status": inv.status
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.patch("/{invitation_id}")
async def update_invitation(
    invitation_id: str,
    req: EditInvitationRequest,
    user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    try:
        updates = req.model_dump(exclude_unset=True)
        inv = await InvitationService.update_invitation(user.id, invitation_id, updates, db)
        return {"id": inv.id, "status": "updated"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/{invitation_id}/send")
async def send_invitation(
    invitation_id: str,
    user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    try:
        inv = await InvitationService.update_status(user.id, invitation_id, "sent", db)
        return {"id": inv.id, "status": "sent"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.delete("/{invitation_id}")
async def delete_invitation(
    invitation_id: str,
    user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    try:
        inv = await InvitationService.update_status(user.id, invitation_id, "cancelled", db)
        inv.is_deleted = True
        await db.commit()
        return {"id": inv.id, "status": "deleted"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
