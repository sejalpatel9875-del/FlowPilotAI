from typing import Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.core.database import get_db
from app.api.v1.endpoints.auth import get_current_user
from app.models.user import UserModel
from app.services.location_service import LocationService

router = APIRouter()


class IPTraceRequest(BaseModel):
    ip_address: Optional[str] = None
    lead_id: Optional[str] = None


@router.get("/lead-map")
async def get_lead_map(
    user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Geographic distribution summary of user's leads."""
    distribution = await LocationService.get_lead_geographic_distribution(user.id, db)
    summary = await LocationService.get_lead_location_summary(user.id, db)
    return {
        "distribution": distribution,
        "summary": summary
    }


@router.post("/trace")
async def trace_location(
    request: IPTraceRequest,
    user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Resolve location context for a given lead or IP address."""
    if request.ip_address:
        geo = LocationService.resolve_ip_location(request.ip_address)
        return {"ip_address": request.ip_address, "resolved_location": geo}

    if request.lead_id:
        from app.models.lead import LeadModel
        from sqlalchemy import select
        res = await db.execute(
            select(LeadModel).where(
                LeadModel.id == request.lead_id,
                LeadModel.user_id == user.id,
                LeadModel.is_deleted == False
            )
        )
        lead = res.scalar_one_or_none()
        if not lead:
            raise HTTPException(status_code=404, detail="Lead not found")
        return {
            "lead_id": lead.id,
            "lead_name": lead.name,
            "location": lead.location,
            "company": lead.company
        }

    raise HTTPException(status_code=400, detail="Provide ip_address or lead_id")


@router.post("/enrich/{lead_id}")
async def enrich_lead_location(
    lead_id: str,
    user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """AI-enrich a lead's location data via LocationTracerAgent."""
    try:
        result = await LocationService.enrich_lead_location(user.id, lead_id, db)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
