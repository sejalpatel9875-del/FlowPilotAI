"""
FlowPilot AI — Comprehensive Permanent Distributed Systems Verification Suite:
Lease Heartbeat, Fencing Tokens, Stale Worker Protection, DLQ, Side-Effect Safety, and Cancellation Races.
"""

import pytest
import asyncio
import time
import uuid
import json
from unittest.mock import AsyncMock
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.user import UserModel
from app.models.workflow import WorkflowModel, WorkflowStepModel, WorkflowApprovalModel, WorkflowEventModel
from app.services.workflow.workflow_queue import WorkflowQueueService, WorkflowJob
from app.services.workflow.workflow_worker import WorkflowWorker
from app.services.workflow.workflow_engine import WorkflowExecutionEngine
from app.services.workflow.workflow_telemetry import WorkflowTelemetry
from app.core.database import AsyncSessionLocal, init_db
from app.core.config import settings
from app.agents.orchestrator import orchestrator


@pytest.fixture(autouse=True)
async def cleanup_env_and_queue():
    """Ensure clean database and queue state before and after each test."""
    await init_db()
    await WorkflowQueueService.clear_all()
    WorkflowWorker._shared_local_locks.clear()
    WorkflowWorker._local_fencing_counters.clear()
    yield
    await WorkflowQueueService.clear_all()
    WorkflowWorker._shared_local_locks.clear()
    WorkflowWorker._local_fencing_counters.clear()


# ============================================================================
# 1. LEASE HEARTBEAT & FENCING TOKEN TESTS
# ============================================================================

@pytest.mark.asyncio
class TestDistributedLeasingAndHeartbeat:
    """Verifies atomic lease acquisition, fencing token generation, heartbeat renewal, and stale worker fencing."""

    async def test_lease_acquisition_and_fencing_token(self):
        worker = WorkflowWorker(worker_id="worker-alpha", lease_seconds=10)
        wf_id = f"wf-lease-{uuid.uuid4().hex[:6]}"

        acquired, token1 = await worker.acquire_lease(wf_id)
        assert acquired is True
        assert token1 is not None
        assert token1 >= 1

        # Verify active ownership
        is_owner = await worker.verify_lease_ownership(wf_id, token1)
        assert is_owner is True

        # Second worker attempts acquisition while lease is active -> Must fail
        worker_beta = WorkflowWorker(worker_id="worker-beta", lease_seconds=10)
        acquired_beta, token_beta = await worker_beta.acquire_lease(wf_id)
        assert acquired_beta is False
        assert token_beta is None

        # Clean release
        await worker.release_lease(wf_id, token1)
        is_owner_after = await worker.verify_lease_ownership(wf_id, token1)
        assert is_owner_after is False

    async def test_lease_heartbeat_renewal(self):
        worker = WorkflowWorker(worker_id="worker-hb", lease_seconds=2)
        wf_id = f"wf-hb-{uuid.uuid4().hex[:6]}"

        acquired, token = await worker.acquire_lease(wf_id)
        assert acquired is True

        # Sleep past half lease timeout and renew
        await asyncio.sleep(0.5)
        renewed = await worker.renew_lease(wf_id, token)
        assert renewed is True

        # Verify ownership is still valid
        assert await worker.verify_lease_ownership(wf_id, token) is True
        await worker.release_lease(wf_id, token)

    async def test_stale_worker_fenced_when_lease_lost(self):
        worker_a = WorkflowWorker(worker_id="worker-a", lease_seconds=1)
        worker_b = WorkflowWorker(worker_id="worker-b", lease_seconds=5)
        wf_id = f"wf-fencing-{uuid.uuid4().hex[:6]}"

        # Worker A acquires lease
        acquired_a, token_a = await worker_a.acquire_lease(wf_id)
        assert acquired_a is True

        # Simulate Worker A stalling / sleeping until lease expires (1.1s)
        await asyncio.sleep(1.1)

        # Worker B acquires expired lease with higher fencing token
        acquired_b, token_b = await worker_b.acquire_lease(wf_id)
        assert acquired_b is True
        assert token_b > token_a

        # Worker A attempts renewal or action with old fencing token -> Must be FENCED
        renewed_a = await worker_a.renew_lease(wf_id, token_a)
        assert renewed_a is False
        assert await worker_a.verify_lease_ownership(wf_id, token_a) is False

        # Worker B remains valid owner
        assert await worker_b.verify_lease_ownership(wf_id, token_b) is True
        await worker_b.release_lease(wf_id, token_b)


# ============================================================================
# 2. QUEUE FAILURE SEMANTICS & DEAD-LETTER QUEUE (DLQ)
# ============================================================================

@pytest.mark.asyncio
class TestQueueFailureSemanticsAndDLQ:
    """Verifies enqueue, dequeue, bounded retries, DLQ routing, and stuck processing reclamation."""

    async def test_enqueue_dequeue_ack_lifecycle(self):
        job = WorkflowJob(
            workflow_id="wf-queue-001",
            user_id="user-queue-001",
            action="execute",
        )
        enqueued = await WorkflowQueueService.enqueue(job)
        assert enqueued is True

        assert await WorkflowQueueService.get_queue_depth() >= 1

        dequeued = await WorkflowQueueService.dequeue(timeout_seconds=0.5)
        assert dequeued is not None
        assert dequeued.workflow_id == "wf-queue-001"
        assert dequeued.last_dequeued_at is not None

        assert await WorkflowQueueService.get_processing_count() == 1
        acked = await WorkflowQueueService.ack(dequeued)
        assert acked is True
        assert await WorkflowQueueService.get_processing_count() == 0

    async def test_dead_letter_queue_after_max_retries(self):
        job = WorkflowJob(
            workflow_id="wf-dlq-001",
            user_id="user-dlq-001",
            action="execute",
            retry_count=0
        )
        # Retries 1, 2, 3
        assert await WorkflowQueueService.retry(job, delay_seconds=0.01) is True
        assert await WorkflowQueueService.retry(job, delay_seconds=0.01) is True
        assert await WorkflowQueueService.retry(job, delay_seconds=0.01) is True

        # 4th retry exceeds max attempts -> Routes to DLQ
        routed_to_dlq = await WorkflowQueueService.retry(job, delay_seconds=0.01)
        assert routed_to_dlq is False

        dlq_depth = await WorkflowQueueService.get_dlq_depth()
        assert dlq_depth == 1

        dlq_jobs = await WorkflowQueueService.get_dlq_jobs(limit=10)
        assert len(dlq_jobs) == 1
        assert dlq_jobs[0].workflow_id == "wf-dlq-001"
        assert dlq_jobs[0].retry_count >= 3

    async def test_stuck_processing_reclamation(self):
        job = WorkflowJob(
            job_id="job-stuck-123",
            workflow_id="wf-stuck-001",
            user_id="user-stuck-001",
            action="execute",
            last_dequeued_at=time.time() - 200.0  # Idle for 200s
        )
        WorkflowQueueService._in_memory_processing[job.job_id] = job

        reclaimed = await WorkflowQueueService.reclaim_stuck_processing_jobs(max_idle_seconds=60.0)
        assert reclaimed == 1
        assert job.job_id not in WorkflowQueueService._in_memory_processing
        assert await WorkflowQueueService.get_queue_depth() == 1

    async def test_production_redis_unavailable_raises_safely(self, monkeypatch):
        # In production mode, volatile in-memory fallback must be rejected
        monkeypatch.setattr(settings, "ENVIRONMENT", "production")
        from app.core.redis import redis_client
        monkeypatch.setattr(redis_client, "connected", False)

        job = WorkflowJob(workflow_id="wf-prod-fail", user_id="user-prod", action="execute")
        with pytest.raises(RuntimeError) as exc_info:
            await WorkflowQueueService.enqueue(job)
        assert "Cannot enqueue durable workflow job" in str(exc_info.value)
        assert "in production" in str(exc_info.value)


# ============================================================================
# 3. SIDE-EFFECT SAFETY & CANCELLATION RACE TESTS
# ============================================================================

@pytest.mark.asyncio
class TestSideEffectSafetyAndCancellationRaces:
    """Verifies that no side effect executes under missing approval, cancellation, or stale worker conditions."""

    async def test_side_effect_prevented_if_cancelled(self):
        user_id = f"user_canc_{uuid.uuid4().hex[:6]}"
        wf_id = f"wf_canc_{uuid.uuid4().hex[:6]}"

        async with AsyncSessionLocal() as db:
            db.add(UserModel(id=user_id, email=f"{user_id}@flowpilot.ai", password_hash="dummy", full_name="Test User", is_active=True, is_verified=True))
            wf = WorkflowModel(
                id=wf_id,
                user_id=user_id,
                title="Cancelled Workflow",
                goal="Send outreach email",
                status="CANCELLED",
                total_steps=1,
                completed_steps=0,
            )
            step = WorkflowStepModel(
                id=str(uuid.uuid4()),
                workflow_id=wf_id,
                user_id=user_id,
                step_key="step_1",
                step_order=0,
                agent_name="OutreachAgent",
                action="send_outreach",
                is_side_effect=True,
                status="PLANNED",
            )
            db.add(wf)
            db.add(step)
            await db.commit()

        # Attempt execution on cancelled workflow
        async with AsyncSessionLocal() as db:
            res_wf = await WorkflowExecutionEngine.execute_graph(wf_id, user_id, db)
            assert res_wf.status == "CANCELLED"

            # Verify step was never executed
            res_step = (await db.execute(select(WorkflowStepModel).where(WorkflowStepModel.workflow_id == wf_id))).scalar_one()
            assert res_step.status == "PLANNED"

    async def test_side_effect_prevented_if_worker_fenced(self):
        user_id = f"user_fence_{uuid.uuid4().hex[:6]}"
        wf_id = f"wf_fence_{uuid.uuid4().hex[:6]}"

        async with AsyncSessionLocal() as db:
            db.add(UserModel(id=user_id, email=f"{user_id}@flowpilot.ai", password_hash="dummy", full_name="Test User", is_active=True, is_verified=True))
            wf = WorkflowModel(
                id=wf_id,
                user_id=user_id,
                title="Fenced Worker Workflow",
                goal="Dispatch campaign",
                status="RUNNING",
                total_steps=1,
                completed_steps=0,
            )
            step = WorkflowStepModel(
                id=str(uuid.uuid4()),
                workflow_id=wf_id,
                user_id=user_id,
                step_key="step_1",
                step_order=0,
                agent_name="OutreachAgent",
                action="send_outreach",
                is_side_effect=True,
                status="PLANNED",
            )
            db.add(wf)
            db.add(step)
            await db.commit()

        # Simulated stale lease verifier returning False
        async def stale_lease_verifier():
            return False

        async with AsyncSessionLocal() as db:
            res_wf = await WorkflowExecutionEngine.execute_graph(
                wf_id, user_id, db, lease_verifier=stale_lease_verifier
            )
            # Step should not have executed
            res_step = (await db.execute(select(WorkflowStepModel).where(WorkflowStepModel.workflow_id == wf_id))).scalar_one()
            assert res_step.status == "PLANNED"

            # STALE_WORKER_FENCED event must be recorded
            events = (await db.execute(select(WorkflowEventModel).where(WorkflowEventModel.workflow_id == wf_id))).scalars().all()
            event_types = [e.event_type for e in events]
            assert "STALE_WORKER_FENCED" in event_types

    async def test_cancellation_race_halts_subsequent_steps(self, monkeypatch):
        user_id = f"user_race_{uuid.uuid4().hex[:6]}"
        wf_id = f"wf_race_{uuid.uuid4().hex[:6]}"

        async with AsyncSessionLocal() as db:
            db.add(UserModel(id=user_id, email=f"{user_id}@flowpilot.ai", password_hash="dummy", full_name="Test User", is_active=True, is_verified=True))
            wf = WorkflowModel(
                id=wf_id,
                user_id=user_id,
                title="Race Workflow",
                goal="Analyze leads then send outreach",
                status="RUNNING",
                total_steps=2,
                completed_steps=0,
            )
            s1 = WorkflowStepModel(
                id=str(uuid.uuid4()),
                workflow_id=wf_id,
                user_id=user_id,
                step_key="step_1",
                step_order=0,
                agent_name="LeadAgent",
                action="analyze_leads",
                status="PLANNED",
            )
            s2 = WorkflowStepModel(
                id=str(uuid.uuid4()),
                workflow_id=wf_id,
                user_id=user_id,
                step_key="step_2",
                step_order=1,
                agent_name="OutreachAgent",
                action="send_outreach",
                depends_on_json=json.dumps(["step_1"]),
                is_side_effect=True,
                status="PLANNED",
            )
            db.add(wf)
            db.add(s1)
            db.add(s2)
            await db.commit()

        # Mock agent 1 to mutate workflow status to CANCELLED during step 1
        async def cancel_mid_flight(user_id, prompt, db, **kwargs):
            wf_to_cancel = await db.get(WorkflowModel, wf_id)
            if wf_to_cancel:
                wf_to_cancel.status = "CANCELLED"
            return {"output": "Step 1 completed before cancellation noticed."}

        mock_agent = AsyncMock()
        mock_agent.run = cancel_mid_flight
        monkeypatch.setattr(orchestrator, "get_agent", lambda name: mock_agent)

        async with AsyncSessionLocal() as db:
            res_wf = await WorkflowExecutionEngine.execute_graph(wf_id, user_id, db)
            assert res_wf.status == "CANCELLED"

            # Step 2 must never have started
            res_s2 = (await db.execute(select(WorkflowStepModel).where(WorkflowStepModel.workflow_id == wf_id, WorkflowStepModel.step_key == "step_2"))).scalar_one()
            assert res_s2.status == "PLANNED"


# ============================================================================
# 4. MOCKED MULTI-WORKER FENCING & RESUMPTION TEST
# ============================================================================

@pytest.mark.asyncio
class TestMockedMultiWorkerSimulation:
    """Simulates two workers contending for the same workflow: Worker A stalls, Worker B takes over, Worker A is blocked."""

    async def test_mocked_multi_worker_fencing_scenario(self, monkeypatch):
        mock_agent = AsyncMock()
        mock_agent.run = AsyncMock(return_value={"output": "Processed step."})
        monkeypatch.setattr(orchestrator, "get_agent", lambda name: mock_agent)

        user_id = f"user_mw_{uuid.uuid4().hex[:6]}"
        wf_id = f"wf_mw_{uuid.uuid4().hex[:6]}"

        async with AsyncSessionLocal() as db:
            db.add(UserModel(id=user_id, email=f"{user_id}@flowpilot.ai", password_hash="dummy", full_name="Multi Worker User", is_active=True, is_verified=True))
            wf = WorkflowModel(
                id=wf_id,
                user_id=user_id,
                title="Multi Worker Workflow",
                goal="Execute workflow across contending workers",
                status="RUNNING",
                total_steps=2,
                completed_steps=0,
            )
            s1 = WorkflowStepModel(
                id=str(uuid.uuid4()),
                workflow_id=wf_id,
                user_id=user_id,
                step_key="step_1",
                step_order=0,
                agent_name="ResearchAgent",
                action="research_market",
                status="PLANNED",
            )
            s2 = WorkflowStepModel(
                id=str(uuid.uuid4()),
                workflow_id=wf_id,
                user_id=user_id,
                step_key="step_2",
                step_order=1,
                agent_name="AnalyticsAgent",
                action="generate_analytics_report",
                depends_on_json=json.dumps(["step_1"]),
                status="PLANNED",
            )
            db.add(wf)
            db.add(s1)
            db.add(s2)
            await db.commit()

        worker_a = WorkflowWorker(worker_id="worker-A", lease_seconds=1)
        worker_b = WorkflowWorker(worker_id="worker-B", lease_seconds=10)

        # 1. Worker A acquires lease
        acquired_a, token_a = await worker_a.acquire_lease(wf_id)
        assert acquired_a is True

        # 2. Worker A stalls (simulate network partition / pause)
        await asyncio.sleep(1.1)

        # 3. Worker B processes job (reclaiming expired lease with new token)
        job_b = WorkflowJob(workflow_id=wf_id, user_id=user_id, action="execute")
        success_b = await worker_b.process_job(job_b)
        assert success_b is True

        # 4. Worker A wakes up and tries to renew/verify with stale token -> Must be rejected safely
        is_owner_a = await worker_a.verify_lease_ownership(wf_id, token_a)
        assert is_owner_a is False

        # 5. Verify final state is completed by Worker B without duplication
        async with AsyncSessionLocal() as db:
            res_wf = await db.get(WorkflowModel, wf_id)
            assert res_wf.status == "COMPLETED"
            assert res_wf.completed_steps == 2
