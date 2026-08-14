import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_analytics_overview_and_chart_data(async_client: AsyncClient):
    # 1. Register & Login
    await async_client.post("/api/v1/auth/register", json={
        "email": "analytics_user@flowpilot.ai",
        "password": "Password123!",
        "fullName": "Analytics Analyst"
    })
    login_res = await async_client.post("/api/v1/auth/login", json={
        "email": "analytics_user@flowpilot.ai",
        "password": "Password123!"
    })
    token = login_res.cookies["flowpilot_session"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Get Real Database Analytics Overview
    overview_res = await async_client.get("/api/v1/analytics/overview", headers=headers)
    assert overview_res.status_code == 200
    data = overview_res.json()

    assert "summaryCards" in data
    assert "trackedDimensions" in data
    assert data["summaryCards"]["leads"] >= 0
    assert data["trackedDimensions"]["leadConversion"]["total"] >= 0

    # 3. Get Chart Datasets
    charts_res = await async_client.get("/api/v1/analytics/charts", headers=headers)
    assert charts_res.status_code == 200
    charts = charts_res.json()

    assert "leadFunnel" in charts
    assert "weeklyProductivity" in charts
    assert "learningProgress" in charts
    assert "clientPipeline" in charts
    assert "agentActivity" in charts
    assert len(charts["leadFunnel"]) == 5
    assert len(charts["weeklyProductivity"]) == 7
