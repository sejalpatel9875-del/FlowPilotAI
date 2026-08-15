from typing import Dict, Any, Optional
from app.agents.base_agent import BaseAgent, AgentMetadata
from app.agents.context_builder import AgentContextBuilder
from app.services.llm_service import LLMService
from app.services.llm.base_provider import LLMRequest


class OutreachAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            AgentMetadata(
                name="OutreachAgent",
                description="Personalized outreach drafting and cold email campaign strategy.",
                purpose="Draft high-converting outreach email drafts and value propositions for qualified leads.",
                system_policy=(
                    "You are OutreachAgent, FlowPilot AI's messaging and campaign drafting agent. "
                    "Craft highly persuasive, professional outreach drafts strictly as recommendations. "
                    "Do NOT automatically send emails, dispatch messages, or communicate externally."
                ),
                allowed_tools=["READ_LEADS", "READ_COMPANY_INFO", "CREATE_OUTREACH_DRAFT"],
                allowed_data_scopes=["leads", "companies", "outreach_messages"],
                risk_level="MEDIUM"
            )
        )

    async def get_context(self, user_id: str, prompt: str, db: Any) -> Dict[str, Any]:
        context_str = await AgentContextBuilder.build_outreach_context(user_id, prompt, db)
        return {"context_text": context_str}

    async def run(self, user_id: str, prompt: str, db: Any, request_id: Optional[str] = None) -> Dict[str, Any]:
        sanitized_prompt = self.validate_input(prompt)
        ctx = await self.get_context(user_id, sanitized_prompt, db)

        full_prompt = f"Outreach Target & Vault Context:\n{ctx['context_text']}\n\nUser Instruction:\n{sanitized_prompt}"
        req = LLMRequest(
            prompt=full_prompt,
            system_prompt=self.system_policy,
            model="nvidia/nemotron-3-ultra-550b-a55b",
            temperature=0.4
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
