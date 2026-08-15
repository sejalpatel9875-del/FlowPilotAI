import abc
import time
import uuid
import logging
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

from app.services.security_guard_service import SensitiveDataFilter

logger = logging.getLogger("flowpilot.agents")


class AgentMetadata(BaseModel):
    name: str
    description: str
    purpose: str
    system_policy: str
    allowed_tools: List[str] = Field(default_factory=list)
    allowed_data_scopes: List[str] = Field(default_factory=list)
    risk_level: str = "LOW"  # LOW, MEDIUM, HIGH, CRITICAL


class BaseAgent(abc.ABC):
    def __init__(self, metadata: AgentMetadata):
        self.metadata = metadata
        self.name = metadata.name
        self.description = metadata.description
        self.purpose = metadata.purpose
        self.system_policy = metadata.system_policy
        self.allowed_tools = metadata.allowed_tools
        self.allowed_data_scopes = metadata.allowed_data_scopes
        self.risk_level = metadata.risk_level

    def validate_input(self, user_prompt: str) -> str:
        """Validate and sanitize input prompt prior to execution."""
        if not user_prompt or not user_prompt.strip():
            raise ValueError(f"Agent '{self.name}' received an empty prompt.")
        sanitized_prompt, _ = SensitiveDataFilter.redact_sensitive_data(user_prompt)
        return sanitized_prompt

    def validate_output(self, raw_output: str) -> str:
        """Validate and redact any sensitive data or CoT from output."""
        if not raw_output:
            return "Agent generated no output."

        # Redact secrets, passwords, or API keys
        sanitized_output, _ = SensitiveDataFilter.redact_sensitive_data(raw_output)

        # Strip internal CoT or XML tags
        if "<think>" in sanitized_output:
            import re
            sanitized_output = re.sub(r"<think>.*?</think>", "", sanitized_output, flags=re.DOTALL)

        return sanitized_output.strip()

    @abc.abstractmethod
    async def get_context(self, user_id: str, prompt: str, db: Any) -> Dict[str, Any]:
        """Build tenant-scoped context strictly filtered by user_id."""
        pass

    @abc.abstractmethod
    async def run(self, user_id: str, prompt: str, db: Any, request_id: Optional[str] = None) -> Dict[str, Any]:
        """Execute agent task."""
        pass
