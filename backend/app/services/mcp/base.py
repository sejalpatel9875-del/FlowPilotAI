from enum import Enum
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class RiskLevel(str, Enum):
    LOW = "LOW"            # Read-only queries, search, public math
    MEDIUM = "MEDIUM"      # Internal state modifications (tasks, reminders)
    HIGH = "HIGH"          # External communications (emails, Slack messages)
    CRITICAL = "CRITICAL"  # Destructive actions (database deletion, credential rotation)


class MCPTool(BaseModel):
    name: str = Field(..., description="Unique tool name identifier")
    description: str = Field(..., description="Tool description")
    server_name: str = Field(default="FlowPilot Core Tools", description="Parent MCP server")
    input_schema: Dict[str, Any] = Field(default_factory=dict, description="JSON Schema for inputs")
    output_schema: Dict[str, Any] = Field(default_factory=dict, description="JSON Schema for outputs")
    risk_level: RiskLevel = Field(default=RiskLevel.LOW, description="Tool risk level")
    required_permissions: List[str] = Field(default_factory=list, description="Required RBAC permissions")
    enabled: bool = Field(default=True, description="Whether tool is active")


class MCPServer(BaseModel):
    id: str
    name: str
    description: str
    status: str = "connected"
    version: str = "1.0.0"
    tools_count: int = 0


class ToolExecutionResult(BaseModel):
    execution_id: str
    tool_name: str
    executed_by_agent: str
    risk_level: RiskLevel
    status: str  # completed, needs_approval, rejected, failed
    result_data: Optional[Dict[str, Any]] = None
    requires_approval: bool = False
    action_to_approve: Optional[str] = None
    error: Optional[str] = None
