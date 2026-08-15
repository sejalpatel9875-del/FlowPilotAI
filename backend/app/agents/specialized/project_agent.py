from typing import Dict, Any, Optional
from app.agents.base_agent import BaseAgent, AgentMetadata
from app.agents.context_builder import AgentContextBuilder
from app.services.llm_service import LLMService
from app.services.llm.base_provider import LLMRequest


class ProjectAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            AgentMetadata(
                name="ProjectAgent",
                description="Project milestone breakdown, task prioritization, and deliverable tracking.",
                purpose="Break down projects into actionable tasks, detect blockers, and track delivery progress.",
                system_policy=(
                    "You are ProjectAgent, FlowPilot AI's project management and task breakdown agent. "
                    "Analyze user's active projects and tasks. Recommend task breakdowns, milestone priorities, and blocker resolutions."
                ),
                allowed_tools=["READ_PROJECTS", "READ_TASKS", "CREATE_TASK_RECOMMENDATION"],
                allowed_data_scopes=["projects", "tasks"],
                risk_level="LOW"
            )
        )

    async def get_context(self, user_id: str, prompt: str, db: Any) -> Dict[str, Any]:
        context_str = await AgentContextBuilder.build_project_context(user_id, prompt, db)
        return {"context_text": context_str}

    async def run(self, user_id: str, prompt: str, db: Any, request_id: Optional[str] = None) -> Dict[str, Any]:
        sanitized_prompt = self.validate_input(prompt)
        ctx = await self.get_context(user_id, sanitized_prompt, db)

        full_prompt = f"Project & Task Context:\n{ctx['context_text']}\n\nUser Instruction:\n{sanitized_prompt}"
        req = LLMRequest(
            prompt=full_prompt,
            system_prompt=self.system_policy,
            model="nvidia/nemotron-3-ultra-550b-a55b",
            temperature=0.3
        )

        res = await LLMService.generate(req=req, user_id=user_id, db=db, provider_name="nvidia")
        clean_text = self.validate_output(res.text)

        return {
            "agent_name": self.name,
            "status": "COMPLETED",
            "output": clean_text,
            "data_scopes_accessed": self.allowed_data_scopes,
            "risk_level": self.risk_level
        }
