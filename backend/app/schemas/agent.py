from typing import Optional
from pydantic import BaseModel, ConfigDict


class AgentActivityBase(BaseModel):
    agentId: str
    agentName: str
    action: str
    status: str = "idle"
    details: Optional[str] = None
    requiresApproval: bool = False
    timestamp: str


class AgentActivityCreate(AgentActivityBase):
    pass


class AgentActivityResponse(AgentActivityBase):
    id: str

    model_config = ConfigDict(from_attributes=True)
