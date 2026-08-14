from typing import Dict, List, Optional
from app.services.mcp.base import MCPTool, MCPServer, RiskLevel


class MCPRegistry:
    def __init__(self):
        self.servers: Dict[str, MCPServer] = {
            "core": MCPServer(id="core", name="FlowPilot Core Tools Server", description="Built-in CRM, RAG, and Workflow automation tools", status="connected", tools_count=5),
            "github": MCPServer(id="github", name="GitHub MCP Server", description="Code repository inspection, issue creation, and pull request tracking", status="connected", tools_count=2),
            "slack": MCPServer(id="slack", name="Slack MCP Server", description="Team messaging, channel alerts, and direct notifications", status="connected", tools_count=2),
            "stripe": MCPServer(id="stripe", name="Stripe MCP Server", description="Invoice generation, subscription tracking, and payment link creation", status="connected", tools_count=2),
        }

        self.tools: Dict[str, MCPTool] = {
            # LOW RISK TOOLS (Read-only, search, calculations)
            "knowledge_search": MCPTool(
                name="knowledge_search",
                description="Search untrusted document chunks in RAG Knowledge Vault",
                server_name="FlowPilot Core Tools Server",
                risk_level=RiskLevel.LOW,
                required_permissions=["USER"],
                input_schema={"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]},
            ),
            "lead_search": MCPTool(
                name="lead_search",
                description="Query CRM leads and prospect score metrics",
                server_name="FlowPilot Core Tools Server",
                risk_level=RiskLevel.LOW,
                required_permissions=["USER"],
                input_schema={"type": "object", "properties": {"status": {"type": "string"}}},
            ),
            "analytics_query": MCPTool(
                name="analytics_query",
                description="Aggregate revenue performance and effective hourly rates",
                server_name="FlowPilot Core Tools Server",
                risk_level=RiskLevel.LOW,
                required_permissions=["USER"],
                input_schema={"type": "object", "properties": {"timeframe": {"type": "string"}}},
            ),

            # MEDIUM RISK TOOLS (Internal state creation/modification)
            "task_creation": MCPTool(
                name="task_creation",
                description="Create a new task or study goal in workplace dashboard",
                server_name="FlowPilot Core Tools Server",
                risk_level=RiskLevel.MEDIUM,
                required_permissions=["USER"],
                input_schema={"type": "object", "properties": {"title": {"type": "string"}}, "required": ["title"]},
            ),
            "reminder_set": MCPTool(
                name="reminder_set",
                description="Schedule a follow-up reminder for a project milestone",
                server_name="FlowPilot Core Tools Server",
                risk_level=RiskLevel.MEDIUM,
                required_permissions=["USER"],
                input_schema={"type": "object", "properties": {"days": {"type": "integer"}}},
            ),
            "proposal_create": MCPTool(
                name="proposal_create",
                description="Generate formal project proposal document draft",
                server_name="FlowPilot Core Tools Server",
                risk_level=RiskLevel.MEDIUM,
                required_permissions=["USER"],
                input_schema={"type": "object", "properties": {"lead_name": {"type": "string"}, "amount": {"type": "number"}}},
            ),

            # HIGH RISK TOOLS (External message sending, email dispatch) -> Requires Human Approval!
            "email_send": MCPTool(
                name="email_send",
                description="Send cold email pitch or follow-up to external client address",
                server_name="FlowPilot Core Tools Server",
                risk_level=RiskLevel.HIGH,
                required_permissions=["USER"],
                input_schema={"type": "object", "properties": {"recipient": {"type": "string"}, "body": {"type": "string"}}, "required": ["recipient"]},
            ),
            "slack_post": MCPTool(
                name="slack_post",
                description="Post notification message to external Slack channel",
                server_name="Slack MCP Server",
                risk_level=RiskLevel.HIGH,
                required_permissions=["USER"],
                input_schema={"type": "object", "properties": {"channel": {"type": "string"}, "message": {"type": "string"}}},
            ),

            # CRITICAL RISK TOOLS (Database deletion, credential access) -> Requires Explicit Admin Confirmation!
            "database_delete": MCPTool(
                name="database_delete",
                description="Delete persistent records from database storage",
                server_name="FlowPilot Core Tools Server",
                risk_level=RiskLevel.CRITICAL,
                required_permissions=["ADMIN"],
                input_schema={"type": "object", "properties": {"table": {"type": "string"}, "id": {"type": "string"}}},
            ),
            "credential_access": MCPTool(
                name="credential_access",
                description="Access third-party integration secret credentials",
                server_name="FlowPilot Core Tools Server",
                risk_level=RiskLevel.CRITICAL,
                required_permissions=["ADMIN"],
                input_schema={"type": "object", "properties": {"provider": {"type": "string"}}},
            ),
        }

    def get_tool(self, tool_name: str) -> Optional[MCPTool]:
        return self.tools.get(tool_name.lower())

    def toggle_tool(self, tool_name: str, enabled: bool) -> MCPTool:
        tool = self.get_tool(tool_name)
        if not tool:
            raise ValueError(f"MCP Tool '{tool_name}' not found.")
        tool.enabled = enabled
        return tool


# Global MCPRegistry singleton
mcp_registry = MCPRegistry()
