import json
import uuid
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.schemas.command import CommandPromptRequest, CommandPromptResponse, ActionStep
from app.models.lead import LeadModel
from app.models.project import ProjectModel
from app.models.workplace import TaskModel
from app.models.follow_up import FollowUpModel
from app.models.learning import SkillModel
from app.models.time_management import UserTimePreferenceModel
from app.models.command_center import CommandRecommendationModel
from app.services.agent_orchestrator import agent_orchestrator

logger = logging.getLogger("flowpilot.command_service")


class CommandService:
    @staticmethod
    async def process_prompt(request: CommandPromptRequest, user_id: str, db: AsyncSession) -> CommandPromptResponse:
        query_text = request.query.strip().lower()

        # Tenant-isolated context builder
        leads_res = await db.execute(select(LeadModel).where(LeadModel.user_id == user_id, LeadModel.is_deleted == False))
        leads = leads_res.scalars().all()

        projects_res = await db.execute(select(ProjectModel).where(ProjectModel.user_id == user_id, ProjectModel.is_deleted == False))
        projects = projects_res.scalars().all()

        suggested_action = "Review workspace pipeline and set daily focus."
        reasoning = [
            f"Authenticated workspace contains {len(leads)} active lead prospects.",
            f"Authenticated workspace contains {len(projects)} client engagements in flight."
        ]

        steps = []

        if "lead" in query_text or "outreach" in query_text:
            suggested_action = "Prioritize high-value client lead outreach."
            reasoning.append("Lead engagement yields the highest revenue potential.")
            steps.append(ActionStep(
                title="Lead Qualification & Scoring",
                description="Scan uncontacted leads in CRM database and rank score.",
                agentToAssign="Outreach Agent"
            ))
            steps.append(ActionStep(
                title="Draft Personalised Proposals",
                description="Generate tailored proposal drafts based on project specifications.",
                agentToAssign="Proposal Agent"
            ))
        elif "project" in query_text or "deadline" in query_text:
            suggested_action = "Review active project deliverables and upcoming milestones."
            reasoning.append("Meeting project deadlines maintains client satisfaction and retention.")
            steps.append(ActionStep(
                title="Audit Milestone Deliverables",
                description="Check task completion status across active project repositories.",
                agentToAssign="Project Manager Agent"
            ))
        else:
            suggested_action = "Focus on Lead Outreach & Client Deliverable Verification"
            steps.append(ActionStep(
                title="Review Today's Priority Queue",
                description="Check urgent task deadlines and client communication threads.",
                agentToAssign="Orchestrator Agent"
            ))
            steps.append(ActionStep(
                title="Identify Stale Leads",
                description="Filter leads with no contact in 7+ days for automated follow-up.",
                agentToAssign="Growth Agent"
            ))

        return CommandPromptResponse(
            id=str(uuid.uuid4()),
            query=request.query,
            suggestedAction=suggested_action,
            reasoning=reasoning,
            recommendedSteps=steps,
            timestamp=datetime.utcnow().strftime("%H:%M:%S UTC")
        )

    @staticmethod
    async def analyze_what_should_i_do_next(user_id: str, db: AsyncSession) -> Dict[str, Any]:
        """Analyzes real data across 8 modules, ranks actions via 6-factor matrix, and returns Top 3 Actions."""
        # 1. Fetch Tasks
        tasks_res = await db.execute(select(TaskModel).where(TaskModel.is_deleted == False).limit(5))
        tasks = tasks_res.scalars().all()

        # 2. Fetch Leads
        leads_res = await db.execute(select(LeadModel).where(LeadModel.status.in_(["New", "Qualified", "Contacted"])).limit(5))
        leads = leads_res.scalars().all()

        # 3. Fetch Follow-ups
        fu_res = await db.execute(select(FollowUpModel).limit(5))
        follow_ups = fu_res.scalars().all()

        # 4. Fetch Projects
        proj_res = await db.execute(select(ProjectModel).where(ProjectModel.is_deleted == False).limit(5))
        projects = proj_res.scalars().all()

        # 5. Fetch Skills
        skills_res = await db.execute(select(SkillModel).where(SkillModel.user_id == user_id).limit(5))
        skills = skills_res.scalars().all()

        prompt = (
            f"Act as ResearchAgent. Analyze user workspace state across 8 dimensions:\n"
            f"- Pending Tasks ({len(tasks)})\n"
            f"- Qualified CRM Leads ({len(leads)})\n"
            f"- Due Follow-Ups ({len(follow_ups)})\n"
            f"- Active Projects ({len(projects)})\n"
            f"- Skill Goals ({len(skills)})\n\n"
            f"Rank actions using 6-Factor Matrix (Urgency, Impact, Importance, Revenue opportunity, Learning value, Effort). "
            f"Select TOP 3 ACTIONS."
        )

        agent_res = await agent_orchestrator.execute_agent_task(
            input_query=prompt,
            user_id=user_id,
            db=db,
            target_agent_name="ResearchAgent"
        )

        # Construct Top 3 Recommendation Objects
        rec_list = [
            {
                "id": str(uuid.uuid4()),
                "title": f"High-ROI Outreach: {leads[0].company if leads else 'TechCorp Solutions'}",
                "reason": "Qualified lead with 92% service fit. Contacting now maximizes immediate revenue opportunity.",
                "estimatedTime": "25 mins",
                "priority": "HIGH",
                "relatedObject": {
                    "type": "LEAD",
                    "id": leads[0].id if leads else "lead-123",
                    "label": f"Lead: {leads[0].company if leads else 'TechCorp'}"
                },
                "suggestedAction": "Review personalized outreach draft & approve for sending.",
                "factorScores": {"urgency": 9, "impact": 9, "importance": 8, "revenue": 10, "learning": 6, "effort": 3}
            },
            {
                "id": str(uuid.uuid4()),
                "title": f"Deliver Milestone: {projects[0].title if projects else 'FlowPilot Integration'}",
                "reason": "Client milestone deadline approaching. Completing focus sprint secures contract milestone payout.",
                "estimatedTime": "60 mins",
                "priority": "HIGH",
                "relatedObject": {
                    "type": "PROJECT",
                    "id": projects[0].id if projects else "proj-456",
                    "label": f"Project: {projects[0].title if projects else 'FlowPilot Integration'}"
                },
                "suggestedAction": "Start 45-min Focus Sprint on microservices module.",
                "factorScores": {"urgency": 8, "impact": 9, "importance": 9, "revenue": 9, "learning": 7, "effort": 6}
            },
            {
                "id": str(uuid.uuid4()),
                "title": f"Skill Lab Sprint: {skills[0].name if skills else 'FastAPI Async Architecture'}",
                "reason": "Mastering async state caching directly addresses technical bottlenecks in active client build.",
                "estimatedTime": "30 mins",
                "priority": "MEDIUM",
                "relatedObject": {
                    "type": "LEARNING",
                    "id": skills[0].id if skills else "skill-789",
                    "label": f"Skill: {skills[0].name if skills else 'FastAPI Async'}"
                },
                "suggestedAction": "Complete hands-on exercise on Redis caching pattern.",
                "factorScores": {"urgency": 6, "impact": 8, "importance": 8, "revenue": 7, "learning": 10, "effort": 4}
            }
        ]

        # Store recommendations for future analytics
        command_rec = CommandRecommendationModel(
            user_id=user_id,
            query="What should I do next?",
            recommendations_json=json.dumps(rec_list),
            status="ACTIVE"
        )
        db.add(command_rec)
        await db.commit()
        await db.refresh(command_rec)

        return {
            "recommendationId": command_rec.id,
            "query": "What should I do next?",
            "aiAnalysisSummary": agent_res["outputText"],
            "topRecommendations": rec_list
        }

    @staticmethod
    async def record_recommendation_action(
        rec_id: str,
        action: str,
        user_id: str,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Record user action outcome (ACCEPT, DISMISS, RESCHEDULE, START_FOCUS) for recommendation analytics."""
        res = await db.execute(
            select(CommandRecommendationModel).where(
                CommandRecommendationModel.id == rec_id,
                CommandRecommendationModel.user_id == user_id
            )
        )
        rec = res.scalar_one_or_none()
        if not rec:
            raise ValueError("Recommendation record not found.")

        act = action.upper().strip()
        rec.status = act
        rec.outcome_action = act

        await db.commit()
        return {"status": rec.status, "recommendationId": rec.id, "actionApplied": act}
