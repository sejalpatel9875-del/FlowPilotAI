import pytest
import uuid
from httpx import AsyncClient
from app.models.workflow import WorkflowModel


@pytest.mark.asyncio
class TestWorkflowSSEStreaming:
    """Permanent integration tests verifying SSE real-time streaming endpoint."""

    async def test_stream_workflow_success(self, async_client: AsyncClient):
        """Verify stream yields SSE events for authorized workflow owner."""
        email = f"sse_user_{uuid.uuid4().hex[:8]}@flowpilot.ai"
        pwd = "Password123!"
        await async_client.post("/api/v1/auth/register", json={"email": email, "password": pwd, "fullName": "SSE User"})
        login = await async_client.post("/api/v1/auth/login", json={"email": email, "password": pwd})
        headers = {"Authorization": f"Bearer {login.cookies['flowpilot_session']}"}

        # Create workflow
        wf_res = await async_client.post(
            "/api/v1/workflows",
            json={"goal": "Analyze leads and generate client proposals"},
            headers=headers
        )
        assert wf_res.status_code == 201
        wf_id = wf_res.json()["id"]

        # Stream workflow
        resp = await async_client.get(
            f"/api/v1/workflows/{wf_id}/stream",
            headers=headers
        )
        assert resp.status_code == 200
        assert "text/event-stream" in resp.headers["content-type"]
        assert "event: connected" in resp.text
        assert wf_id in resp.text

    async def test_stream_workflow_cross_tenant_blocked(self, async_client: AsyncClient):
        """Verify Tenant B cannot stream Tenant A's workflow."""
        email_a = f"usera_sse_{uuid.uuid4().hex[:6]}@flowpilot.ai"
        await async_client.post("/api/v1/auth/register", json={"email": email_a, "password": "Password123!", "fullName": "User A"})
        login_a = await async_client.post("/api/v1/auth/login", json={"email": email_a, "password": "Password123!"})
        headers_a = {"Authorization": f"Bearer {login_a.cookies['flowpilot_session']}"}

        wf_res = await async_client.post("/api/v1/workflows", json={"goal": "User A confidential workflow"}, headers=headers_a)
        wf_id = wf_res.json()["id"]

        # Register User B
        email_b = f"userb_sse_{uuid.uuid4().hex[:6]}@flowpilot.ai"
        await async_client.post("/api/v1/auth/register", json={"email": email_b, "password": "Password123!", "fullName": "User B"})
        login_b = await async_client.post("/api/v1/auth/login", json={"email": email_b, "password": "Password123!"})
        headers_b = {"Authorization": f"Bearer {login_b.cookies['flowpilot_session']}"}

        # User B attempts to stream User A's workflow
        resp = await async_client.get(
            f"/api/v1/workflows/{wf_id}/stream",
            headers=headers_b
        )
        assert resp.status_code == 404
        assert "not found or access denied" in resp.json()["detail"].lower()

    async def test_stream_unauthenticated_rejected(self, async_client: AsyncClient):
        """Verify unauthenticated requests to stream endpoint receive 401."""
        resp = await async_client.get("/api/v1/workflows/dummy-wf-id/stream")
        assert resp.status_code == 401
