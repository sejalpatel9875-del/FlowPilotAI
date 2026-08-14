import time
import uuid
import logging
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.services.agents.base_agent import BaseAgent, AgentRunResult
from app.services.agents.agent_implementations import (
    LeadAgent,
    ResearchAgent,
    OutreachAgent,
    FollowUpAgent,
    ProposalAgent,
    ProjectAgent,
    TimeManagementAgent,
    LearningAgent,
    AnalyticsAgent,
    SecurityAgent,
)
from app.models.agent_engine import AgentRunModel, AgentMessageModel, ToolCallModel
from app.models.agent_memory import AgentMemoryModel

logger = logging.getLogger("flowpilot.agent_orchestrator")


class AgentOrchestrator:
    def __init__(self):
        # Register 10 specialized agent instances
        self.agents: Dict[str, BaseAgent] = {
            "leadagent": LeadAgent(),
            "researchagent": ResearchAgent(),
            "outreachagent": OutreachAgent(),
            "followupagent": FollowUpAgent(),
            "proposalagent": ProposalAgent(),
            "projectagent": ProjectAgent(),
            "timemanagementagent": TimeManagementAgent(),
            "learningagent": LearningAgent(),
            "analyticsagent": AnalyticsAgent(),
            "securityagent": SecurityAgent(),
        }

    def get_agent(self, agent_name: str) -> BaseAgent:
        key = agent_name.lower().replace(" ", "").replace("_", "")
        if key not in self.agents:
            raise ValueError(f"Unknown agent '{agent_name}'. Available agents: {list(self.agents.keys())}")
        return self.agents[key]

    def route_request_to_agent(self, query: str, requested_agent: Optional[str] = None) -> BaseAgent:
        """Determines best target agent based on query intent if not explicitly specified."""
        if requested_agent:
            return self.get_agent(requested_agent)

        q = query.lower()
        if "lead" in q or "prospect" in q or "client score" in q: return self.agents["leadagent"]
        if "research" in q or "document" in q or "search" in q: return self.agents["researchagent"]
        if "email" in q or "outreach" in q or "pitch" in q: return self.agents["outreachagent"]
        if "follow" in q or "remind" in q: return self.agents["followupagent"]
        if "proposal" in q or "pricing" in q or "quote" in q: return self.agents["proposalagent"]
        if "project" in q or "milestone" in q: return self.agents["projectagent"]
        if "time" in q or "calendar" in q or "schedule" in q: return self.agents["timemanagementagent"]
        if "learn" in q or "skill" in q or "study" in q: return self.agents["learningagent"]
        if "analytics" in q or "revenue" in q or "metric" in q: return self.agents["analyticsagent"]
        if "security" in q or "audit" in q or "login" in q: return self.agents["securityagent"]

        return self.agents["researchagent"]

    async def retrieve_scoped_memory(self, user_id: str, agent_name: str, db: AsyncSession) -> Dict[str, str]:
        """Retrieves scoped memory for specific user and agent."""
        res = await db.execute(
            select(AgentMemoryModel).where(
                AgentMemoryModel.user_id == user_id,
                AgentMemoryModel.agent_name == agent_name
            )
        )
        memories = res.scalars().all()
        return {m.memory_key: m.memory_value for m in memories}

    async def execute_agent_task(
        self,
        input_query: str,
        user_id: str,
        db: AsyncSession,
        target_agent_name: Optional[str] = None,
        requested_tool: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Complete orchestration pipeline: intent -> permission check -> memory -> run -> validate -> log."""
        start_time = time.time()
        agent = self.route_request_to_agent(input_query, requested_agent=target_agent_name)

        # Explicit Permission Check if specific tool requested
        if requested_tool:
            agent.check_permission(requested_tool)

        # Retrieve Scoped Memory
        scoped_memory = await self.retrieve_scoped_memory(user_id, agent.name, db)

        # Execute Agent
        result: AgentRunResult = await agent.run(input_query, user_id, context={"memory": scoped_memory})

        # Validate Output
        if not agent.validate(result.output_text):
            result.success = False
            result.error = "Agent output validation failed."

        latency_ms = round((time.time() - start_time) * 1000, 2)
        run_status = "needs_approval" if result.requires_approval else ("completed" if result.success else "failed")

        # Create AgentRun record
        run_id = f"run_{uuid.uuid4().hex[:12]}"
        db_run = AgentRunModel(
            id=run_id,
            user_id=user_id,
            agent_id=agent.name,
            status=run_status,
            input_query=input_query,
        )
        db.add(db_run)
        await db.flush()

        # Create Messages
        msg_user = AgentMessageModel(
            run_id=run_id,
            role="user",
            content=input_query,
        )
        msg_assistant = AgentMessageModel(
            run_id=run_id,
            role="assistant",
            content=result.output_text,
        )
        db.add(msg_user)
        db.add(msg_assistant)

        # Create Tool Calls
        for tool_name in result.tools_used:
            tc = ToolCallModel(
                run_id=run_id,
                tool_name=tool_name,
                tool_args=input_query,
                tool_output=result.reasoning_summary,
                status="completed",
            )
            db.add(tc)

        await db.commit()

        return {
            "runId": run_id,
            "agentName": agent.name,
            "agentDescription": agent.description,
            "status": run_status,
            "inputQuery": input_query,
            "outputText": result.output_text,
            "reasoningSummary": result.reasoning_summary,  # Safe execution summary (no hidden chain-of-thought)
            "toolsUsed": result.tools_used,
            "requiresApproval": result.requires_approval,
            "actionToApprove": result.action_to_approve,
            "permissions": agent.permissions(),
            "latencyMs": latency_ms,
        }


# Global AgentOrchestrator singleton
agent_orchestrator = AgentOrchestrator()
