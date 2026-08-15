from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import UserModel
from app.models.agent_engine import AgentRunModel
from app.agents.orchestrator import orchestrator

router = APIRouter()


class AgentExecuteRequest(BaseModel):
    prompt: Optional[str] = Field(None, description="User request prompt for agent execution")
    query: Optional[str] = Field(None, description="Alias query parameter")
    agentName: Optional[str] = Field(None, description="Target agent name override")


@router.post("/execute")
@router.post("/run")
async def execute_agent_task(
    req: AgentExecuteRequest,
    user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Execute authenticated user prompt through Multi-Agent Orchestrator."""
    prompt_text = req.prompt or req.query
    if not prompt_text or not prompt_text.strip():
        raise HTTPException(status_code=400, detail="Prompt query cannot be empty.")

    try:
        res = await orchestrator.execute_request(
            user_id=user.id,
            prompt=prompt_text,
            db=db,
            target_agent_name=req.agentName
        )
        first_run_id = res["runs"][0]["agent"] if res["runs"] else "run_1"
        latest_run = await db.execute(
            select(AgentRunModel).where(AgentRunModel.user_id == user.id).order_by(AgentRunModel.started_at.desc())
        )
        last_obj = latest_run.scalars().first()

        return {
            "runId": last_obj.id if last_obj else first_run_id,
            "requestId": res["requestId"],
            "agentName": res["agentsExecuted"][0] if res["agentsExecuted"] else "LeadAgent",
            "agentsExecuted": res["agentsExecuted"],
            "status": last_obj.status if last_obj else "completed",
            "totalLatencyMs": res["totalLatencyMs"],
            "finalResponse": res["finalResponse"],
            "outputText": res["finalResponse"],
            "runs": res["runs"]
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent execution failed: {str(e)}")


@router.post("/runs/{run_id}/approve")
async def approve_agent_run(
    run_id: str,
    user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Approve a pending agent run action."""
    res = await db.execute(
        select(AgentRunModel).where(
            AgentRunModel.id == run_id,
            AgentRunModel.user_id == user.id
        )
    )
    run_obj = res.scalar_one_or_none()
    if not run_obj:
        raise HTTPException(status_code=404, detail="Agent run not found or unauthorized.")

    run_obj.status = "completed"
    await db.commit()
    return {"status": "success", "message": f"Agent run '{run_id}' approved successfully."}


@router.get("/dashboard")
async def get_agent_dashboard(
    user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Retrieve visual metrics, status, risk levels, and run counts for all 9 specialized agents."""
    agents_info = []

    for name, agent in orchestrator.agent_registry.items():
        res = await db.execute(
            select(
                func.count(AgentRunModel.id),
                func.avg(AgentRunModel.latency_ms)
            )
            .where(
                AgentRunModel.user_id == user.id,
                AgentRunModel.agent_name == name
            )
        )
        run_count, avg_lat = res.first() or (0, 0)

        agents_info.append({
            "name": agent.name,
            "description": agent.description,
            "purpose": agent.purpose,
            "riskLevel": agent.risk_level,
            "status": "READY",
            "totalRuns": run_count or 0,
            "avgLatencyMs": int(avg_lat or 0),
            "allowedDataScopes": agent.allowed_data_scopes,
            "allowedTools": agent.allowed_tools
        })

    return {"agents": agents_info}


@router.get("/runs")
async def list_agent_runs(
    user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List recent agent execution runs strictly scoped to authenticated user."""
    res = await db.execute(
        select(AgentRunModel)
        .where(AgentRunModel.user_id == user.id)
        .order_by(AgentRunModel.started_at.desc())
        .limit(20)
    )
    runs = res.scalars().all()

    return {
        "runs": [
            {
                "id": r.id,
                "agentName": r.agent_name,
                "requestId": r.request_id,
                "inputSummary": r.input_summary,
                "status": r.status,
                "startedAt": r.started_at.strftime("%Y-%m-%d %H:%M:%S UTC") if r.started_at else None,
                "completedAt": r.completed_at.strftime("%Y-%m-%d %H:%M:%S UTC") if r.completed_at else None,
                "latencyMs": r.latency_ms,
                "outputSummary": r.output_summary
            }
            for r in runs
        ]
    }


@router.get("/runs/{run_id}")
async def get_agent_run_detail(
    run_id: str,
    user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """View detailed agent run record with tenant ownership validation."""
    res = await db.execute(
        select(AgentRunModel)
        .where(
            AgentRunModel.id == run_id,
            AgentRunModel.user_id == user.id
        )
    )
    run_obj = res.scalar_one_or_none()
    if not run_obj:
        raise HTTPException(status_code=404, detail="Agent run not found or unauthorized.")

    return {
        "id": run_obj.id,
        "agentName": run_obj.agent_name,
        "requestId": run_obj.request_id,
        "inputQuery": run_obj.input_query,
        "status": run_obj.status,
        "startedAt": run_obj.started_at.strftime("%Y-%m-%d %H:%M:%S UTC") if run_obj.started_at else None,
        "completedAt": run_obj.completed_at.strftime("%Y-%m-%d %H:%M:%S UTC") if run_obj.completed_at else None,
        "latencyMs": run_obj.latency_ms,
        "errorCode": run_obj.error_code,
        "outputSummary": run_obj.output_summary
    }
