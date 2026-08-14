import logging
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.lead import LeadModel
from app.models.crm import LeadActivityModel
from app.services.agent_orchestrator import agent_orchestrator

logger = logging.getLogger("flowpilot.lead_crm")

PIPELINE_STAGES = [
    "New",
    "Qualified",
    "Researching",
    "Outreach Ready",
    "Contacted",
    "Replied",
    "Meeting",
    "Proposal",
    "Won",
    "Lost",
    "Not Interested"
]


class LeadCRMService:
    @staticmethod
    def calculate_transparent_score(
        service_fit: str = "High",
        industry: str = "Technology",
        has_contact_info: bool = True,
        status: str = "New"
    ) -> Dict[str, Any]:
        """Calculates transparent lead score (0-100) across 5 weighted factors."""
        # Factor 1: Service Fit (25 pts)
        s_fit = (service_fit or "High").lower()
        service_fit_score = 25 if s_fit == "high" else (15 if s_fit == "medium" else 5)

        # Factor 2: Industry Fit (20 pts)
        ind = (industry or "Technology").lower()
        industry_score = 20 if any(k in ind for k in ["tech", "saas", "software"]) else (15 if any(k in ind for k in ["finance", "e-commerce"]) else 10)

        # Factor 3: Opportunity Signals (25 pts)
        opp_score = 22 if status in ["Researching", "Outreach Ready", "Contacted", "Replied", "Meeting", "Proposal", "Won"] else 15

        # Factor 4: Project Potential (15 pts)
        potential_score = 15

        # Factor 5: Available Legitimate Contact Info (15 pts)
        contact_score = 15 if has_contact_info else 5

        total_score = service_fit_score + industry_score + opp_score + potential_score + contact_score

        return {
            "totalScore": min(total_score, 100),
            "breakdown": {
                "serviceFitScore": service_fit_score,
                "industryFitScore": industry_score,
                "opportunitySignalsScore": opp_score,
                "projectPotentialScore": potential_score,
                "contactInfoScore": contact_score,
            }
        }

    @staticmethod
    async def execute_lead_ai_action(
        lead_id: str,
        action_type: str,
        user_id: str,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Executes AI actions on leads and logs auditable entries into lead_activities."""
        res = await db.execute(
            select(LeadModel).where(
                LeadModel.id == lead_id,
                LeadModel.user_id == user_id,
                LeadModel.is_deleted == False
            )
        )
        lead = res.scalar_one_or_none()
        if not lead:
            raise ValueError("Lead record not found or unauthorized.")

        act_type = action_type.lower().strip()

        if act_type == "analyze":
            # Run LeadAgent
            agent_res = await agent_orchestrator.execute_agent_task(
                input_query=f"Analyze ICP fit and conversion potential for lead '{lead.name}' at '{lead.company}'",
                user_id=user_id,
                db=db,
                target_agent_name="LeadAgent"
            )
            scoring_res = LeadCRMService.calculate_transparent_score(
                service_fit=lead.service_fit,
                industry=lead.industry,
                has_contact_info=bool(lead.email),
                status=lead.status
            )
            lead.lead_score = scoring_res["totalScore"]
            lead.verification_status = "Verified"
            lead.notes = (lead.notes or "") + f"\n\n[AI Analysis]: {agent_res['outputText']}"
            output_msg = agent_res["outputText"]
            activity_label = "AI Lead Analysis"

        elif act_type == "opportunity":
            # Run ResearchAgent
            agent_res = await agent_orchestrator.execute_agent_task(
                input_query=f"Find expansion and revenue opportunities for client '{lead.company}' in '{lead.industry}'",
                user_id=user_id,
                db=db,
                target_agent_name="ResearchAgent"
            )
            lead.status = "Researching" if lead.status == "New" else lead.status
            lead.verification_status = "Inferred"
            output_msg = agent_res["outputText"]
            activity_label = "AI Opportunity Search"

        elif act_type == "outreach":
            # Run OutreachAgent
            agent_res = await agent_orchestrator.execute_agent_task(
                input_query=f"Draft cold outreach email pitch for '{lead.name}' at '{lead.company}'",
                user_id=user_id,
                db=db,
                target_agent_name="OutreachAgent"
            )
            lead.status = "Outreach Ready"
            output_msg = agent_res["outputText"]
            activity_label = "AI Outreach Draft"

        elif act_type in ["recommend_next_action", "recommend"]:
            # Recommend Next Action
            agent_res = await agent_orchestrator.execute_agent_task(
                input_query=f"Recommend next sales action for lead '{lead.company}' currently in '{lead.status}' stage",
                user_id=user_id,
                db=db,
                target_agent_name="FollowUpAgent"
            )
            lead.next_action = f"Follow-up: {agent_res['output_text'][:100]}"
            output_msg = f"Recommended Next Action: {agent_res['output_text']}"
            activity_label = "AI Next Action Recommendation"

        else:
            raise ValueError(f"Unsupported AI action '{action_type}'. Allowed: analyze, opportunity, outreach, recommend_next_action.")

        # Log AI action into lead_activities table
        act_model = LeadActivityModel(
            lead_id=lead.id,
            activity_type=act_type,
            description=f"[{activity_label}]: {output_msg[:300]}...",
        )
        db.add(act_model)

        await db.commit()
        await db.refresh(lead)

        return {
            "leadId": lead.id,
            "company": lead.company,
            "status": lead.status,
            "leadScore": lead.lead_score,
            "verificationStatus": lead.verification_status,
            "nextAction": lead.next_action,
            "actionType": act_type,
            "aiOutput": output_msg,
        }
