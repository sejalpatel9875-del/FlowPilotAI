from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.lead import LeadModel
from app.schemas.lead import LeadCreate, LeadResponse


class LeadService:
    @staticmethod
    async def get_all_leads(db: AsyncSession) -> List[LeadResponse]:
        result = await db.execute(select(LeadModel))
        leads = result.scalars().all()
        return [
            LeadResponse(
                id=l.id,
                name=l.name,
                company=l.company,
                email=l.email,
                value=l.value,
                score=l.score,
                status=l.status,
                source=l.source,
            )
            for l in leads
        ]

    @staticmethod
    async def create_lead(lead_in: LeadCreate, db: AsyncSession) -> LeadResponse:
        lead = LeadModel(**lead_in.model_dump())
        db.add(lead)
        await db.commit()
        await db.refresh(lead)
        return LeadResponse(
            id=lead.id,
            name=lead.name,
            company=lead.company,
            email=lead.email,
            value=lead.value,
            score=lead.score,
            status=lead.status,
            source=lead.source,
        )
