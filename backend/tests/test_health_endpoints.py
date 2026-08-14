import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_global_health_endpoint(async_client: AsyncClient):
    res = await async_client.get("/api/v1/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "active"
    assert "version" in data


@pytest.mark.asyncio
async def test_readiness_endpoint(async_client: AsyncClient):
    res = await async_client.get("/api/v1/health/ready")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ready"
    assert data["database"] == "connected"


@pytest.mark.asyncio
async def test_version_endpoint(async_client: AsyncClient):
    res = await async_client.get("/api/v1/health/version")
    assert res.status_code == 200
    data = res.json()
    assert data["version"] == "1.0.0"
    assert "buildSha" in data


@pytest.mark.asyncio
async def test_root_probes(async_client: AsyncClient):
    res_h = await async_client.get("/health")
    assert res_h.status_code == 200
    assert res_h.json()["status"] == "active"

    res_r = await async_client.get("/ready")
    assert res_r.status_code == 200
    assert res_r.json()["status"] == "ready"

    res_v = await async_client.get("/version")
    assert res_v.status_code == 200
    assert res_v.json()["version"] == "1.0.0"
