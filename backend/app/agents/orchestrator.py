import time
import uuid
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.base_agent import BaseAgent
from app.agents.router import IntentRouter
from app.agents.specialized.lead_agent import LeadAgent
from app.agents.specialized.research_agent import ResearchAgent
from app.agents.specialized.outreach_agent import OutreachAgent
from app.agents.specialized.follow_up_agent import FollowUpAgent
from app.agents.specialized.proposal_agent import ProposalAgent
from app.agents.specialized.project_agent import ProjectAgent
from app.agents.specialized.time_management_agent import TimeManagementAgent
from app.agents.specialized.learning_agent import LearningAgent
from app.agents.specialized.analytics_agent import AnalyticsAgent
from app.agents.specialized.invitation_agent import InvitationAgent
from app.agents.specialized.location_tracer_agent import LocationTracerAgent
from app.agents.specialized.reminder_agent import ReminderAgent

from app.models.agent_engine import AgentRunModel
from app.services.audit_log_service import AuditLogService

logger = logging.getLogger("flowpilot.agents.orchestrator")


class AgentOrchestrator:
    # Safety Limits
    MAX_AGENT_DEPTH = 3
    MAX_EXECUTION_TIME_SECONDS = 30
    MAX_AGENT_COUNT_PER_REQUEST = 3

    def __init__(self):
        self.agent_registry: Dict[str, BaseAgent] = {
            "LeadAgent": LeadAgent(),
            "ResearchAgent": ResearchAgent(),
            "OutreachAgent": OutreachAgent(),
            "FollowUpAgent": FollowUpAgent(),
            "ProposalAgent": ProposalAgent(),
            "ProjectAgent": ProjectAgent(),
            "TimeManagementAgent": TimeManagementAgent(),
            "LearningAgent": LearningAgent(),
            "AnalyticsAgent": AnalyticsAgent(),
            "InvitationAgent": InvitationAgent(),
            "LocationTracerAgent": LocationTracerAgent(),
            "ReminderAgent": ReminderAgent(),
        }

    def get_agent(self, agent_name: str) -> Optional[BaseAgent]:
        return self.agent_registry.get(agent_name)

    async def execute_request(
        self,
        user_id: str,
        prompt: str,
        db: AsyncSession,
        request_id: Optional[str] = None,
        target_agent_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """Execute request through multi-agent orchestrator with safety controls."""
        if not user_id:
            raise ValueError("Authentication required: user_id is missing.")

        req_id = request_id or f"req_{uuid.uuid4().hex[:12]}"
        start_time = time.time()

        # 1. Intent Routing or explicit override
        if target_agent_name and self.get_agent(target_agent_name):
            target_agent_names = [target_agent_name]
        else:
            target_agent_names = IntentRouter.route_intent(prompt)

        # Enforce execution limits
        if len(target_agent_names) > self.MAX_AGENT_COUNT_PER_REQUEST:
            target_agent_names = target_agent_names[:self.MAX_AGENT_COUNT_PER_REQUEST]

        execution_results = []
        agent_runs_logged = []

        for depth, agent_name in enumerate(target_agent_names):
            if depth >= self.MAX_AGENT_DEPTH:
                logger.warning(f"Exceeded max agent recursion depth ({self.MAX_AGENT_DEPTH}). Halting chain.")
                break

            # Timeout check
            elapsed = time.time() - start_time
            if elapsed >= self.MAX_EXECUTION_TIME_SECONDS:
                logger.warning(f"Orchestrator timeout reached ({elapsed:.1f}s). Halting chain.")
                break

            agent = self.get_agent(agent_name)
            if not agent:
                logger.warning(f"Agent '{agent_name}' not found in registry.")
                continue

            # Log Run - QUEUED -> RUNNING
            agent_run = AgentRunModel(
                id=str(uuid.uuid4()),
                user_id=user_id,
                agent_name=agent.name,
                request_id=req_id,
                input_query=prompt[:500],
                input_summary=prompt[:200],
                status="RUNNING",
                started_at=datetime.utcnow()
            )
            db.add(agent_run)
            await db.flush()

            agent_start = time.time()
            try:
                res = await agent.run(user_id=user_id, prompt=prompt, db=db, request_id=req_id)
                agent_latency = int((time.time() - agent_start) * 1000)

                run_status = "needs_approval" if agent.name == "OutreachAgent" else "completed"
                agent_run.status = run_status
                agent_run.completed_at = datetime.utcnow()
                agent_run.latency_ms = agent_latency
                agent_run.output_summary = res["output"][:500]

                execution_results.append({
                    "agent": agent.name,
                    "risk_level": agent.risk_level,
                    "output": res["output"],
                    "status": run_status,
                    "latency_ms": agent_latency
                })
                agent_runs_logged.append(agent_run.id)

                # Audit Log
                await AuditLogService.log_event(
                    user_id=user_id,
                    action=f"AGENT_EXECUTION_{agent.name.upper()}",
                    resource_type="AGENT",
                    resource_id=agent_run.id,
                    details={"status": run_status, "latency_ms": agent_latency},
                    db=db
                )
            except Exception as e:
                agent_latency = int((time.time() - agent_start) * 1000)
                agent_run.status = "failed"
                agent_run.completed_at = datetime.utcnow()
                agent_run.latency_ms = agent_latency
                agent_run.error_code = str(e)[:100]
                agent_run.output_summary = f"Execution failed: {str(e)}"

                logger.error(f"Agent '{agent.name}' failed: {str(e)}")
                execution_results.append({
                    "agent": agent.name,
                    "risk_level": agent.risk_level,
                    "output": f"Agent encountered an error: {str(e)}",
                    "latency_ms": agent_latency
                })

        await db.commit()
        total_latency = int((time.time() - start_time) * 1000)

        # Synthesize final response if multi-agent workflow or single agent
        if len(execution_results) == 1:
            final_text = execution_results[0]["output"]
        else:
            sections = [f"### Agent Insight: {item['agent']} ({item['risk_level']} Risk)\n{item['output']}" for item in execution_results]
            final_text = "\n\n".join(sections)

        return {
            "requestId": req_id,
            "agentsExecuted": [item["agent"] for item in execution_results],
            "totalLatencyMs": total_latency,
            "finalResponse": final_text,
            "runs": execution_results,
            "runsLogged": agent_runs_logged
        }


orchestrator = AgentOrchestrator()
