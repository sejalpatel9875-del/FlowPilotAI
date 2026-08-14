import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.services.mcp.registry import mcp_registry
from app.services.mcp.execution_engine import mcp_execution_engine
from app.services.mcp.base import RiskLevel
from app.models.governance import AuditLogModel
from app.models.user import UserModel, RoleModel, UserRoleModel

@pytest.mark.asyncio
async def test_mcp_tool_registry():
    # Verify registered servers
    assert "core" in mcp_registry.servers
    assert "github" in mcp_registry.servers

    # Verify tools across risk levels
    low_tool = mcp_registry.get_tool("knowledge_search")
    assert low_tool is not None
    assert low_tool.risk_level == RiskLevel.LOW

    high_tool = mcp_registry.get_tool("email_send")
    assert high_tool is not None
    assert high_tool.risk_level == RiskLevel.HIGH

    crit_tool = mcp_registry.get_tool("database_delete")
    assert crit_tool is not None
    assert crit_tool.risk_level == RiskLevel.CRITICAL

@pytest.mark.asyncio
async def test_mcp_risk_level_approval_policy(db_session: AsyncSession):
    user = UserModel(email="mcp_user@flowpilot.ai", password_hash="hash", full_name="MCP User")
    db_session.add(user)
    await db_session.commit()

    # 1. LOW Risk tool -> Completed immediately
    res_low = await mcp_execution_engine.execute_tool(
        tool_name="knowledge_search",
        input_args={"query": "AI architecture"},
        user=user,
        agent_name="ResearchAgent",
        db=db_session
    )
    assert res_low.status == "completed"
    assert res_low.requires_approval == False

    # 2. HIGH Risk tool -> Requires Human Approval
    res_high = await mcp_execution_engine.execute_tool(
        tool_name="email_send",
        input_args={"recipient": "client@acme.com", "body": "Pitch"},
        user=user,
        agent_name="OutreachAgent",
        db=db_session
    )
    assert res_high.status == "needs_approval"
    assert res_high.requires_approval == True

@pytest.mark.asyncio
async def test_mcp_critical_admin_role_enforcement(db_session: AsyncSession):
    user_std = UserModel(email="std_user@flowpilot.ai", password_hash="hash", full_name="Std User")
    db_session.add(user_std)
    await db_session.commit()

    # Standard user attempting CRITICAL tool -> PermissionError
    with pytest.raises(PermissionError) as exc:
        await mcp_execution_engine.execute_tool(
            tool_name="credential_access",
            input_args={"provider": "github"},
            user=user_std,
            agent_name="TestAgent",
            db=db_session
        )
    assert "ADMIN" in str(exc.value)

@pytest.mark.asyncio
async def test_mcp_audit_logging(db_session: AsyncSession):
    user = UserModel(email="audit_user@flowpilot.ai", password_hash="hash", full_name="Audit User")
    db_session.add(user)
    await db_session.commit()

    await mcp_execution_engine.execute_tool(
        tool_name="lead_search",
        input_args={"status": "new"},
        user=user,
        agent_name="LeadAgent",
        db=db_session
    )

    # Verify audit entry created
    res = await db_session.execute(select(AuditLogModel).where(AuditLogModel.user_id == user.id))
    logs = res.scalars().all()
    assert len(logs) == 1
    assert "mcp_tool_exec:lead_search" in logs[0].action
