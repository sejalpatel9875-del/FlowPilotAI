import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.learning import SkillModel

@pytest.mark.asyncio
async def test_learning_agent_roadmap_and_recommendations_flow(async_client: AsyncClient):
    # 1. Register & Login
    await async_client.post("/api/v1/auth/register", json={
        "email": "learning_user@flowpilot.ai",
        "password": "Password123!",
        "fullName": "Learning Manager"
    })
    login_res = await async_client.post("/api/v1/auth/login", json={
        "email": "learning_user@flowpilot.ai",
        "password": "Password123!"
    })
    token = login_res.cookies["flowpilot_session"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Create Skill Goal & AI Roadmap
    skill_res = await async_client.post("/api/v1/learning/skills", json={
        "name": "FastAPI Async Architecture",
        "currentLevel": "Intermediate",
        "targetLevel": "Expert",
        "weeklyHours": 10
    }, headers=headers)

    assert skill_res.status_code == 200
    skill_id = skill_res.json()["id"]
    assert skill_res.json()["name"] == "FastAPI Async Architecture"
    assert "curriculum" in skill_res.json()

    # 3. Retrieve Dashboard Analytics & Skills
    dash_res = await async_client.get("/api/v1/learning", headers=headers)
    assert dash_res.status_code == 200
    assert dash_res.json()["dashboardMetrics"]["activeSkillGoals"] >= 1

    # 4. Trigger AI Skill Recommender ("What should I learn next?")
    rec_res = await async_client.post("/api/v1/learning/recommend", headers=headers)
    assert rec_res.status_code == 200
    assert len(rec_res.json()["recommendedSkills"]) >= 1

    # 5. Log Study Hours
    log_res = await async_client.post(f"/api/v1/learning/{skill_id}/log-hours", json={"hours": 2.5}, headers=headers)
    assert log_res.status_code == 200
    assert log_res.json()["loggedHours"] == 15.0  # 12.5 initial + 2.5

    # 6. Submit Assessment Quiz Score
    ass_res = await async_client.post(f"/api/v1/learning/{skill_id}/assessment", json={"scorePercent": 92.5}, headers=headers)
    assert ass_res.status_code == 200
    assert ass_res.json()["assessmentScore"] == 92.5
