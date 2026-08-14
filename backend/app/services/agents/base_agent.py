from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class AgentRunResult(BaseModel):
    agent_name: str
    output_text: str
    reasoning_summary: str
    tools_used: List[str]
    requires_approval: bool = False
    action_to_approve: Optional[str] = None
    success: bool = True
    error: Optional[str] = None


class BaseAgent(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        """Returns unique agent identifier."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Returns human-readable agent description."""
        pass

    @property
    @abstractmethod
    def system_policy(self) -> str:
        """Returns system prompt policy governing agent behavior."""
        pass

    @property
    @abstractmethod
    def allowed_tools(self) -> List[str]:
        """Returns explicit list of tools allowed for this agent."""
        pass

    @property
    @abstractmethod
    def denied_tools(self) -> List[str]:
        """Returns explicit list of tools strictly denied for this agent."""
        pass

    @property
    def memory_policy(self) -> str:
        """Returns scoped memory access policy."""
        return "scoped_user_only"

    def permissions(self) -> Dict[str, List[str]]:
        """Returns explicit permission policy map."""
        return {
            "ALLOW": self.allowed_tools,
            "DENY": self.denied_tools,
        }

    def check_permission(self, action_or_tool: str):
        """Throws PermissionError if action is in DENY list or not in ALLOW list."""
        tool = action_or_tool.lower()
        if any(d.lower() == tool for d in self.denied_tools):
            raise PermissionError(f"Agent '{self.name}' is strictly DENIED permission for action '{action_or_tool}'.")
        if not any(a.lower() == tool for a in self.allowed_tools):
            raise PermissionError(f"Action '{action_or_tool}' is not in the ALLOWED tool list for agent '{self.name}'.")

    def validate(self, output_text: str) -> bool:
        """Validates output text quality and safety."""
        if not output_text or not output_text.strip():
            return False
        return True

    @abstractmethod
    async def run(
        self,
        input_query: str,
        user_id: str,
        context: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> AgentRunResult:
        """Executes agent task and returns AgentRunResult."""
        pass
