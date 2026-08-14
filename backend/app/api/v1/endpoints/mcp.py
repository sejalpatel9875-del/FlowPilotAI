from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import UserModel
from app.models.governance import AuditLogModel
from app.services.mcp.registry import mcp_registry
from app.services.mcp.execution_engine import mcp_execution_engine

router = APIRouter()


class ToggleToolRequest(BaseModel):
    enabled: bool = Field(..., description="Enable or disable tool")


class TestToolRequest(BaseModel):
    inputArgs: Dict[str, Any] = Field(default_factory=dict, description="Test input parameters")
    agentName: str = Field(default="TestAgent", description="Invoking agent name")


@router.get("/servers")
async def list_mcp_servers(user: UserModel = Depends(get_current_user)):
    """List connected MCP Servers."""
    return {"servers": list(mcp_registry.servers.values())}


@router.get("/tools")
async def list_mcp_tools(user: UserModel = Depends(get_current_user)):
    """List all registered MCP Tools with Risk Levels and Schemas."""
    tools_list = []
    for tool in mcp_registry.tools.values():
        tools_list.append({
            "name": tool.name,
            "description": tool.description,
            "serverName": tool.server_name,
            "riskLevel": tool.risk_level.value,
            "requiredPermissions": tool.required_permissions,
            "inputSchema": tool.input_schema,
            "outputSchema": tool.output_schema,
            "enabled": tool.enabled,
        })
    return {"tools": tools_list}


@router.post("/tools/{tool_name}/toggle")
async def toggle_mcp_tool(
    tool_name: str,
    req: ToggleToolRequest,
    user: UserModel = Depends(get_current_user)
):
    """Enable or disable specific MCP Tool."""
    try:
        updated_tool = mcp_registry.toggle_tool(tool_name, req.enabled)
        return {"status": "success", "toolName": updated_tool.name, "enabled": updated_tool.enabled}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/tools/{tool_name}/test")
async def test_mcp_tool_execution(
    tool_name: str,
    req: TestToolRequest,
    request: Request,
    user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Safely test execution of an MCP Tool through execution engine."""
    client_ip = request.client.host if request.client else "127.0.0.1"
    try:
        res = await mcp_execution_engine.execute_tool(
            tool_name=tool_name,
            input_args=req.inputArgs,
            user=user,
            agent_name=req.agentName,
            db=db,
            ip_address=client_ip
        )
        return res
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Tool test execution failed: {str(e)}")


@router.get("/executions")
async def list_mcp_tool_audit_logs(
    user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Retrieve audit log history of MCP Tool executions."""
    res = await db.execute(
        select(AuditLogModel)
        .where(AuditLogModel.action.like("mcp_tool_exec:%"))
        .order_by(AuditLogModel.created_at.desc())
        .limit(20)
    )
    logs = res.scalars().all()

    return {
        "executions": [
            {
                "executionId": l.resource_id,
                "action": l.action.replace("mcp_tool_exec:", ""),
                "ipAddress": l.ip_address,
                "details": l.details,
                "timestamp": l.created_at.strftime("%Y-%m-%d %H:%M:%S UTC"),
            }
            for l in logs
        ]
    }
