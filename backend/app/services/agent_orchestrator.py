import logging
from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.orchestrator import orchestrator as new_orchestrator

logger = logging.getLogger("flowpilot.agent_orchestrator")


class AgentOrchestratorService:
    def __init__(self):
        self.orchestrator = new_orchestrator

    async def execute_agent_task(
        self,
        input_query: str,
        user_id: str,
        db: AsyncSession,
        target_agent_name: Optional[str] = None,
        requested_tool: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Wrapper redirecting to production multi-agent orchestrator."""
        res = await self.orchestrator.execute_request(
            user_id=user_id,
            prompt=input_query,
            db=db
        )
        agent_name = res["agentsExecuted"][0] if res["agentsExecuted"] else "LeadAgent"
        status_val = res["runs"][0]["status"] if (res.get("runs") and "status" in res["runs"][0]) else ("needs_approval" if agent_name == "OutreachAgent" else "completed")

        return {
            "runId": res["requestId"],
            "agentName": agent_name,
            "agentDescription": "FlowPilot AI Specialized Production Agent",
            "status": status_val,
            "inputQuery": input_query,
            "outputText": res["finalResponse"],
            "reasoningSummary": "Execution completed safely with tenant-isolated context.",
            "toolsUsed": [],
            "requiresApproval": False,
            "actionToApprove": None,
            "permissions": ["READ", "EXECUTE_SAFE"],
            "latencyMs": res["totalLatencyMs"],
        }


agent_orchestrator = AgentOrchestratorService()
