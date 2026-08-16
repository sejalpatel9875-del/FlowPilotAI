"""
FlowPilot AI — Comprehensive Permanent Test Suite for Phase 9:
Distributed Workflow Execution, Durable Background Worker Queue, Concurrency Leases, and Crash Recovery.
"""

import pytest
import asyncio
import time
import uuid
import json
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.user import UserModel
from app.models.workflow import WorkflowModel, WorkflowStepModel, WorkflowApprovalModel, WorkflowEventModel
from app.services.workflow.workflow_queue import WorkflowQueueService, WorkflowJob
from app.services.workflow.workflow_worker import WorkflowWorker
from app.services.workflow.workflow_engine import WorkflowExecutionEngine
from app.core.database import AsyncSessionLocal, init_db


@pytest.fixture(autouse=True)
async def cleanup_queue():
    """Ensure clean database and queue state before and after each test."""
    await init_db()
    await WorkflowQueueService.clear_all()
    yield
    await WorkflowQueueService.clear_all()


# ============================================================================
# 1. QUEUE OPERATIONS TESTS
# ============================================================================

@pytest.mark.asyncio
class TestWorkflowQueueOperations:
    """Verifies durable enqueue, dequeue, ack, and bounded retry behavior."""

    async def test_enqueue_dequeue_ack_lifecycle(self):
        job = WorkflowJob(
            workflow_id="wf-test-001",
            user_id="user-test-001",
            action="execute",
            payload={"test": True}
        )
        enqueued = await WorkflowQueueService.enqueue(job)
        assert enqueued is True

        depth = await WorkflowQueueService.get_queue_depth()
        assert depth >= 1

        dequeued = await WorkflowQueueService.dequeue(timeout_seconds=1.0)
        assert dequeued is not None
        assert dequeued.workflow_id == "wf-test-001"
        assert dequeued.user_id == "user-test-001"

        acked = await WorkflowQueueService.ack(dequeued)
        assert acked is True

    async def test_queue_retry_bounded_limit(self):
        job = WorkflowJob(
            workflow_id="wf-retry-test",
            user_id="user-retry-test",
            action="execute",
            retry_count=0
        )
        # 1st retry
        res1 = await WorkflowQueueService.retry(job, delay_seconds=0.01)
        assert res1 is True
        assert job.retry_count == 1

        # 2nd retry
        res2 = await WorkflowQueueService.retry(job, delay_seconds=0.01)
        assert res2 is True
        assert job.retry_count == 2

        # 3rd retry
        res3 = await WorkflowQueueService.retry(job, delay_seconds=0.01)
        assert res3 is True
        assert job.retry_count == 3

        # 4th retry -> Exceeds max retries (3) -> Must return False
        res4 = await WorkflowQueueService.retry(job, delay_seconds=0.01)
        assert res4 is False


# ============================================================================
# 2. WORKER CONCURRENCY & LEASING TESTS
# ============================================================================

@pytest.mark.asyncio
class TestWorkerConcurrencyAndLeases:
    """Verifies distributed lease locks prevent duplicate simultaneous executions."""

    async def test_worker_lease_acquisition_and_release(self):
        worker = WorkflowWorker(worker_id="test-worker-alpha", lease_seconds=10)
        wf_id = f"wf-lease-{uuid.uuid4().hex[:6]}"

        # Acquire lock
        acquired = await worker.acquire_lease(wf_id)
        assert acquired is True

        # Second worker attempts to acquire same lease -> Must fail
        worker_beta = WorkflowWorker(worker_id="test-worker-beta", lease_seconds=10)
        acquired_beta = await worker_beta.acquire_lease(wf_id)
        assert acquired_beta is False

        # Release lock
        await worker.release_lease(wf_id)

        # Worker beta can now acquire
        acquired_beta_after = await worker_beta.acquire_lease(wf_id)
        assert acquired_beta_after is True
        await worker_beta.release_lease(wf_id)

    async def test_worker_contention_safe_requeue(self):
        worker_1 = WorkflowWorker(worker_id="worker-1", lease_seconds=10)
        worker_2 = WorkflowWorker(worker_id="worker-2", lease_seconds=10)
        wf_id = f"wf-contention-{uuid.uuid4().hex[:6]}"

        # Worker 1 holds lease
        await worker_1.acquire_lease(wf_id)

        job = WorkflowJob(workflow_id=wf_id, user_id="user-123", action="execute")
        # Worker 2 attempts to process -> Should detect contention and return False
        processed = await worker_2.process_job(job)
        assert processed is False

        await worker_1.release_lease(wf_id)


# ============================================================================
# 3. CRASH RECOVERY & IDEMPOTENCY TESTS
# ============================================================================

@pytest.mark.asyncio
class TestWorkerCrashRecoveryAndIdempotency:
    """Verifies workers recover crashed workflows without re-executing completed DAG steps."""

    async def test_crash_recovery_resumption(self):
        user_id = f"user_crash_{uuid.uuid4().hex[:6]}"
        wf_id = f"wf_crash_{uuid.uuid4().hex[:6]}"

        async with AsyncSessionLocal() as db:
            # Ensure user exists
            db.add(UserModel(id=user_id, email=f"{user_id}@flowpilot.ai", password_hash="dummy", full_name="Test User", is_active=True, is_verified=True))
            
            # Workflow with Step 1 COMPLETED and Step 2 PLANNED
            wf = WorkflowModel(
                id=wf_id,
                user_id=user_id,
                title="Crash Recovery Workflow",
                goal="Test recovery without duplicate step execution",
                status="RUNNING",
                total_steps=2,
                completed_steps=1,
            )
            db.add(wf)

            s1 = WorkflowStepModel(
                id=str(uuid.uuid4()),
                workflow_id=wf_id,
                user_id=user_id,
                step_key="step_1",
                step_order=0,
                agent_name="ResearchAgent",
                action="research_market",
                status="COMPLETED",
                output_data_json=json.dumps({"agent": "ResearchAgent", "output": "Pre-computed market research", "summary": "Pre-computed"}),
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
            db.add(s1)
            db.add(s2)
            await db.commit()

        # New worker acquires and processes workflow
        worker = WorkflowWorker(worker_id="recovery-worker-01")
        job = WorkflowJob(workflow_id=wf_id, user_id=user_id, action="execute")
        success = await worker.process_job(job)
        assert success is True

        # Verify Step 1 remained COMPLETED with original data and Step 2 completed
        async with AsyncSessionLocal() as db:
            res_wf = await db.get(WorkflowModel, wf_id)
            assert res_wf.status == "COMPLETED"
            assert res_wf.completed_steps == 2

            res_steps = (await db.execute(
                select(WorkflowStepModel).where(WorkflowStepModel.workflow_id == wf_id).order_by(WorkflowStepModel.step_order)
            )).scalars().all()
            assert res_steps[0].status == "COMPLETED"
            assert "Pre-computed market research" in res_steps[0].output_data_json
            assert res_steps[1].status == "COMPLETED"


# ============================================================================
# 4. MOCKED CONCURRENCY BENCHMARK (10 & 25 CONCURRENT WORKFLOWS)
# ============================================================================

@pytest.mark.asyncio
class TestMockedConcurrencyBenchmark:
    """Load and concurrency benchmark verifying multi-worker queue throughput safely with mocked agents."""

    async def test_10_concurrent_workflow_throughput(self, monkeypatch):
        from unittest.mock import AsyncMock
        from app.agents.orchestrator import orchestrator

        # Mock agent to prevent overloading external LLM and eliminate latency in benchmark
        mock_agent = AsyncMock()
        mock_agent.run = AsyncMock(return_value={"output": "Fast benchmark analysis completed."})
        monkeypatch.setattr(orchestrator, "get_agent", lambda name: mock_agent)

        worker_pool = [WorkflowWorker(worker_id=f"bench-worker-{i}") for i in range(4)]
        workflow_count = 10
        user_id = f"bench_user_{uuid.uuid4().hex[:6]}"

        # Seed workflows & enqueue jobs
        async with AsyncSessionLocal() as db:
            db.add(UserModel(id=user_id, email=f"{user_id}@flowpilot.ai", password_hash="dummy", full_name="Test User", is_active=True, is_verified=True))
            for i in range(workflow_count):
                w_id = f"bench-wf-10-{i}-{uuid.uuid4().hex[:4]}"
                wf = WorkflowModel(
                    id=w_id,
                    user_id=user_id,
                    title=f"Benchmark Workflow #{i}",
                    goal="Execute benchmark task",
                    status="RUNNING",
                    total_steps=1,
                    completed_steps=0,
                )
                step = WorkflowStepModel(
                    id=str(uuid.uuid4()),
                    workflow_id=w_id,
                    user_id=user_id,
                    step_key="step_1",
                    step_order=0,
                    agent_name="AnalyticsAgent",
                    action="generate_analytics_report",
                    status="PLANNED",
                )
                db.add(wf)
                db.add(step)
                await WorkflowQueueService.enqueue(WorkflowJob(workflow_id=w_id, user_id=user_id, action="execute"))
            await db.commit()

        start_time = time.time()

        # Run worker pool until all jobs are processed
        async def worker_loop(w: WorkflowWorker):
            for _ in range(25):
                has_job = await w.run_once(timeout_seconds=0.05)
                if not has_job:
                    await asyncio.sleep(0.02)

        await asyncio.gather(*[worker_loop(w) for w in worker_pool])
        duration = time.time() - start_time

        # Verify all 10 workflows reached COMPLETED
        async with AsyncSessionLocal() as db:
            res = (await db.execute(
                select(WorkflowModel).where(WorkflowModel.user_id == user_id)
            )).scalars().all()
            completed = sum(1 for w in res if w.status == "COMPLETED")
            assert completed == workflow_count
            assert duration < 10.0  # Must complete quickly with mocked agent
