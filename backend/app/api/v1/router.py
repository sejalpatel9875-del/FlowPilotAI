from fastapi import APIRouter
from app.api.v1.endpoints import (
    health,
    auth,
    command,
    leads,
    projects,
    agents,
    ai,
    knowledge,
    mcp,
    outreach,
    follow_ups,
    time_management,
    learning,
    automations,
    security,
    analytics,
    invitations,
    location,
    reminders
)

api_router = APIRouter()

api_router.include_router(health.router, prefix="/health", tags=["Health"])
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication & RBAC"])
api_router.include_router(ai.router, prefix="/ai", tags=["LLM Gateway & AI Services"])
api_router.include_router(knowledge.router, prefix="/knowledge", tags=["RAG Knowledge Vault"])
api_router.include_router(mcp.router, prefix="/mcp", tags=["MCP Tool Architecture"])
api_router.include_router(outreach.router, prefix="/outreach", tags=["Personalized Outreach Engine"])
api_router.include_router(follow_ups.router, prefix="/follow-ups", tags=["Intelligent Follow-Up Engine"])
api_router.include_router(time_management.router, prefix="/time", tags=["AI Time Management & Planner"])
api_router.include_router(learning.router, prefix="/learning", tags=["AI Learning Agent & Skill Accelerator"])
api_router.include_router(automations.router, prefix="/automations", tags=["FlowPilot Automation Engine"])
api_router.include_router(security.router, prefix="/security", tags=["Security Center & Measurable Controls"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["FlowPilot Analytics System"])
api_router.include_router(command.router, prefix="/command", tags=["AI Command Center"])
api_router.include_router(leads.router, prefix="/leads", tags=["Leads CRM"])
api_router.include_router(projects.router, prefix="/projects", tags=["Projects"])
api_router.include_router(agents.router, prefix="/agents", tags=["AI Agents"])
api_router.include_router(invitations.router, prefix="/invitations", tags=["Invitation Agent"])
api_router.include_router(location.router, prefix="/location", tags=["Location Tracer Agent"])
api_router.include_router(reminders.router, prefix="/reminders", tags=["Reminder Agent"])
