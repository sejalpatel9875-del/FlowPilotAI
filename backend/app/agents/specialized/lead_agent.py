from typing import Dict, Any, Optional
from app.agents.base_agent import BaseAgent, AgentMetadata
from app.agents.context_builder import AgentContextBuilder
from app.services.llm_service import LLMService
from app.services.llm.base_provider import LLMRequest


class LeadAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            AgentMetadata(
                name="LeadAgent",
                description="Lead qualification, scoring, and high-value client opportunity analysis.",
                purpose="Analyze CRM lead pipeline, score lead readiness, and recommend targeted qualification strategies.",
                system_policy=(
                    "You are LeadAgent, FlowPilot AI's specialized lead qualification and CRM intelligence agent. "
                    "Analyze authorized user leads strictly from provided context. Recommend lead status updates, lead scoring, "
                    "and qualification steps. Do NOT execute external actions or communicate directly with third parties."
                ),
                allowed_tools=["READ_LEADS", "READ_COMPANIES", "READ_KNOWLEDGE", "CREATE_ANALYSIS"],
                allowed_data_scopes=["leads", "companies", "contacts", "knowledge"],
                risk_level="LOW"
            )
        )

    async def get_context(self, user_id: str, prompt: str, db: Any) -> Dict[str, Any]:
        context_str = await AgentContextBuilder.build_lead_context(user_id, prompt, db)
        return {"context_text": context_str}

    async def run(self, user_id: str, prompt: str, db: Any, request_id: Optional[str] = None) -> Dict[str, Any]:
        sanitized_prompt = self.validate_input(prompt)
        ctx = await self.get_context(user_id, sanitized_prompt, db)

        full_prompt = f"Lead Data & Vault Context:\n{ctx['context_text']}\n\nUser Instruction:\n{sanitized_prompt}"
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
