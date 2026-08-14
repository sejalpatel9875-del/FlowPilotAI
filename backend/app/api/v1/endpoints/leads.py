from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from pydantic import BaseModel, Field, EmailStr

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import UserModel
from app.models.lead import LeadModel
from app.models.crm import LeadActivityModel
from app.services.lead_crm_service import LeadCRMService, PIPELINE_STAGES

router = APIRouter()


class CreateLeadRequest(BaseModel):
    name: str = Field(..., description="Lead contact full name")
    company: str = Field(..., description="Company name")
    email: EmailStr = Field(..., description="Contact email address")
    website: Optional[str] = "https://acme.com"
    industry: Optional[str] = "Technology"
    location: Optional[str] = "San Francisco, CA"
    source: Optional[str] = "Organic"
    serviceFit: Optional[str] = "High"  # High, Medium, Low
    status: Optional[str] = "New"
    notes: Optional[str] = None
    nextAction: Optional[str] = "Schedule discovery call"
    verificationStatus: Optional[str] = "Verified"  # Verified, Inferred, Unknown


class UpdateLeadRequest(BaseModel):
    status: Optional[str] = None
    nextAction: Optional[str] = None
    notes: Optional[str] = None
    serviceFit: Optional[str] = None
    verificationStatus: Optional[str] = None


class LeadAIActionRequest(BaseModel):
    actionType: str = Field(..., description="analyze, opportunity, outreach, or recommend_next_action")


@router.get("")
async def list_leads(
    status_filter: Optional[str] = Query(None, alias="status"),
    search: Optional[str] = Query(None),
    user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List authenticated user's CRM leads with status filtering and text search."""
    query = select(LeadModel).where(
        LeadModel.user_id == user.id,
        LeadModel.is_deleted == False
    )

    if status_filter:
        query = query.where(LeadModel.status == status_filter)

    if search:
        s = f"%{search}%"
        query = query.where(
            or_(
                LeadModel.name.ilike(s),
                LeadModel.company.ilike(s),
                LeadModel.email.ilike(s),
                LeadModel.industry.ilike(s),
            )
        )

    query = query.order_by(LeadModel.created_at.desc())
    res = await db.execute(query)
    leads = res.scalars().all()

    return {
        "pipelineStages": PIPELINE_STAGES,
        "totalLeads": len(leads),
        "leads": [
            {
                "id": l.id,
                "name": l.name,
                "company": l.company,
                "email": l.email,
                "website": l.website,
                "industry": l.industry,
                "location": l.location,
                "source": l.source,
                "serviceFit": l.service_fit,
                "leadScore": l.lead_score,
                "status": l.status,
                "notes": l.notes,
                "nextAction": l.next_action,
                "verificationStatus": l.verification_status,
                "createdAt": l.created_at.strftime("%Y-%m-%d %H:%M:%S UTC"),
            }
            for l in leads
        ]
    }


@router.post("")
async def create_lead(
    req: CreateLeadRequest,
    user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create new CRM lead scoped strictly to authenticated user."""
    scoring = LeadCRMService.calculate_transparent_score(
        service_fit=req.serviceFit or "High",
        industry=req.industry or "Technology",
        has_contact_info=bool(req.email),
        status=req.status or "New"
    )

    lead = LeadModel(
        user_id=user.id,  # Never trust client-supplied user_id
        name=req.name,
        company=req.company,
        email=req.email,
        website=req.website,
        industry=req.industry,
        location=req.location,
        source=req.source,
        service_fit=req.serviceFit,
        lead_score=scoring["totalScore"],
        status=req.status if req.status in PIPELINE_STAGES else "New",
        notes=req.notes,
        next_action=req.nextAction,
        verification_status=req.verificationStatus or "Verified",
    )
    db.add(lead)
    await db.flush()

    # Initial Activity Log
    act = LeadActivityModel(
        lead_id=lead.id,
        activity_type="created",
        description=f"Lead created from source '{lead.source}' with score {lead.lead_score}.",
    )
    db.add(act)

    await db.commit()
    await db.refresh(lead)

    return {
        "id": lead.id,
        "name": lead.name,
        "company": lead.company,
        "email": lead.email,
        "leadScore": lead.lead_score,
        "scoreBreakdown": scoring["breakdown"],
        "status": lead.status,
        "verificationStatus": lead.verification_status,
    }


@router.get("/{lead_id}")
async def get_lead_detail(
    lead_id: str,
    user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Retrieve detailed lead profile, score breakdown, and activity timeline with ownership check."""
    res = await db.execute(
        select(LeadModel).where(
            LeadModel.id == lead_id,
            LeadModel.user_id == user.id,
            LeadModel.is_deleted == False
        )
    )
    lead = res.scalar_one_or_none()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found or unauthorized.")

    scoring = LeadCRMService.calculate_transparent_score(
        service_fit=lead.service_fit,
        industry=lead.industry,
        has_contact_info=bool(lead.email),
        status=lead.status
    )

    act_res = await db.execute(
        select(LeadActivityModel)
        .where(LeadActivityModel.lead_id == lead.id)
        .order_by(LeadActivityModel.created_at.desc())
    )
    activities = act_res.scalars().all()

    return {
        "id": lead.id,
        "name": lead.name,
        "company": lead.company,
        "email": lead.email,
        "website": lead.website,
        "industry": lead.industry,
        "location": lead.location,
        "source": lead.source,
        "serviceFit": lead.service_fit,
        "leadScore": lead.lead_score,
        "scoreBreakdown": scoring["breakdown"],
        "status": lead.status,
        "notes": lead.notes,
        "nextAction": lead.next_action,
        "verificationStatus": lead.verification_status,
        "createdAt": lead.created_at.strftime("%Y-%m-%d %H:%M:%S UTC"),
        "activities": [
            {
                "id": a.id,
                "type": a.activity_type,
                "description": a.description,
                "timestamp": a.created_at.strftime("%Y-%m-%d %H:%M:%S UTC"),
            }
            for a in activities
        ]
    }


@router.patch("/{lead_id}")
async def update_lead(
    lead_id: str,
    req: UpdateLeadRequest,
    user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update lead status, next_action, or notes with ownership check."""
    res = await db.execute(
        select(LeadModel).where(
            LeadModel.id == lead_id,
            LeadModel.user_id == user.id,
            LeadModel.is_deleted == False
        )
    )
    lead = res.scalar_one_or_none()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found or unauthorized.")

    if req.status:
        if req.status not in PIPELINE_STAGES:
            raise HTTPException(status_code=400, detail=f"Invalid pipeline stage. Allowed: {PIPELINE_STAGES}")
        old_status = lead.status
        lead.status = req.status
        act = LeadActivityModel(
            lead_id=lead.id,
            activity_type="status_change",
            description=f"Pipeline stage moved from '{old_status}' -> '{req.status}'.",
        )
        db.add(act)

    if req.nextAction:
        lead.next_action = req.nextAction

    if req.notes is not None:
        lead.notes = req.notes

    if req.verificationStatus:
        lead.verification_status = req.verificationStatus

    await db.commit()
    await db.refresh(lead)

    return {"status": "success", "leadId": lead.id, "currentStatus": lead.status, "nextAction": lead.next_action}


@router.delete("/{lead_id}")
async def delete_lead(
    lead_id: str,
    user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Soft delete lead record with ownership check."""
    res = await db.execute(
        select(LeadModel).where(
            LeadModel.id == lead_id,
            LeadModel.user_id == user.id,
            LeadModel.is_deleted == False
        )
    )
    lead = res.scalar_one_or_none()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found or unauthorized.")

    lead.is_deleted = True
    await db.commit()
    return {"status": "success", "message": f"Lead '{lead.company}' soft-deleted."}


@router.post("/{lead_id}/ai-action")
async def execute_lead_ai_action_endpoint(
    lead_id: str,
    req: LeadAIActionRequest,
    user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Execute AI action on lead with strict ownership check."""
    try:
        res = await LeadCRMService.execute_lead_ai_action(
            lead_id=lead_id,
            action_type=req.actionType,
            user_id=user.id,
            db=db
        )
        return res
    except ValueError as e:
        raise HTTPException(status_code=404 if "not found" in str(e).lower() else 400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lead AI action execution failed: {str(e)}")
