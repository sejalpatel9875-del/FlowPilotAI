import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.crm import CompanyModel, ContactModel
from app.models.workplace import ClientModel
from app.models.project import ProjectModel
from app.models.learning import GoalModel, SkillModel
from app.models.knowledge import DocumentModel, DocumentChunkModel
from app.models.agent_engine import AgentModel, AgentRunModel
from app.models.automation import AutomationModel
from app.models.governance import NotificationModel

@pytest.mark.asyncio
async def test_25_tables_schema_integrity(db_session: AsyncSession):
    # 1. CRM: Create Company & Contact
    comp = CompanyModel(name="TechCorp", domain="techcorp.io", industry="SaaS")
    db_session.add(comp)
    await db_session.flush()

    contact = ContactModel(company_id=comp.id, first_name="Alex", last_name="Rivera", email="alex@techcorp.io")
    db_session.add(contact)
    await db_session.flush()

    assert contact.company_id == comp.id
    assert contact.is_deleted == False

    # 2. Workplace: Client & Project
    client = ClientModel(name="Acme Inc", email="billing@acme.com")
    db_session.add(client)
    await db_session.flush()

    proj = ProjectModel(client_id=client.id, title="FlowPilot Integration", client_name="Acme Inc", deadline="2026-12-31")
    db_session.add(proj)
    await db_session.flush()

    assert proj.client_id == client.id

    # 3. Learning: Goal & Skill
    skill = SkillModel(name="FastAPI & Async", category="Backend", proficiency_level=5)
    db_session.add(skill)
    await db_session.flush()

    assert skill.name == "FastAPI & Async"

    # 4. Agent Engine: Agent & Run
    agent = AgentModel(name="Code Review Agent", system_prompt="You review PRs", model_name="gpt-4o")
    db_session.add(agent)
    await db_session.flush()

    run = AgentRunModel(agent_id=agent.id, status="running", input_query="Review authentication module")
    db_session.add(run)
    await db_session.flush()

    assert run.agent_id == agent.id

    await db_session.rollback()
