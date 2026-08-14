from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class CommandPromptRequest(BaseModel):
    query: str = Field(..., description="Natural language request or command prompt")
    context: Optional[Dict[str, Any]] = Field(default=None, description="Optional execution context")


class ActionStep(BaseModel):
    title: str
    description: str
    agentToAssign: Optional[str] = None


class CommandPromptResponse(BaseModel):
    id: str
    query: str
    suggestedAction: str
    reasoning: List[str]
    recommendedSteps: List[ActionStep]
    timestamp: str
