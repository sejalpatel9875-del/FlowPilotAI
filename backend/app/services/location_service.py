import logging
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models.lead import LeadModel

logger = logging.getLogger("flowpilot.location")


class LocationService:

    @staticmethod
    async def get_lead_location_summary(user_id: str, db: AsyncSession) -> Dict[str, Any]:
        """Aggregate lead locations for geographic summary."""
        res = await db.execute(
            select(LeadModel).where(
                LeadModel.user_id == user_id,
                LeadModel.is_deleted == False
            )
        )
        leads = res.scalars().all()
        location_counts: Dict[str, int] = {}
        for lead in leads:
            loc = lead.location or "Unknown"
            location_counts[loc] = location_counts.get(loc, 0) + 1

        return {
            "locations": location_counts,
            "total_leads_with_location": sum(location_counts.values())
        }

    @staticmethod
    def resolve_ip_location(ip_address: str) -> Dict[str, str]:
        """Lightweight internal IP-to-region mapper (no external API calls)."""
        if ip_address.startswith("10.") or ip_address.startswith("192.168.") or ip_address.startswith("172."):
            return {"city": "Internal", "region": "Private Network", "country": "Local"}
        elif ip_address == "127.0.0.1" or ip_address == "::1":
            return {"city": "Localhost", "region": "Local", "country": "Local"}
        return {"city": "Unknown", "region": "Unknown", "country": "Unknown"}

    @staticmethod
    async def get_lead_geographic_distribution(user_id: str, db: AsyncSession) -> List[Dict[str, Any]]:
        """Returns lead count and pipeline value grouped by location."""
        res = await db.execute(
            select(LeadModel).where(
                LeadModel.user_id == user_id,
                LeadModel.is_deleted == False
            )
        )
        leads = res.scalars().all()

        geo_map: Dict[str, Dict[str, Any]] = {}
        for lead in leads:
            loc = lead.location or "Unknown"
            if loc not in geo_map:
                geo_map[loc] = {"location": loc, "lead_count": 0, "total_pipeline_value": 0.0}
            geo_map[loc]["lead_count"] += 1
            geo_map[loc]["total_pipeline_value"] += float(lead.value or 0)

        return list(geo_map.values())

    @staticmethod
    async def enrich_lead_location(user_id: str, lead_id: str, db: AsyncSession) -> Dict[str, Any]:
        """Enrich a lead's location data using the LocationTracerAgent."""
        from app.agents.orchestrator import orchestrator

        res = await db.execute(
            select(LeadModel).where(
                LeadModel.id == lead_id,
                LeadModel.user_id == user_id,
                LeadModel.is_deleted == False
            )
        )
        lead = res.scalar_one_or_none()
        if not lead:
            raise ValueError("Lead not found")

        prompt = f"Analyze and enrich the location context for lead '{lead.name}' at '{lead.company}' currently located at '{lead.location}'. Provide timezone, region insights, and best outreach timing."
        result = await orchestrator.execute_request(
            user_id=user_id,
            prompt=prompt,
            db=db,
            target_agent_name="LocationTracerAgent"
        )
        return {
            "lead_id": lead_id,
            "current_location": lead.location,
            "enrichment": result.get("finalResponse", ""),
            "status": "enriched"
        }
