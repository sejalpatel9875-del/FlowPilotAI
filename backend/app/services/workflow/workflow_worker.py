import os
import time
import uuid
import asyncio
import logging
import signal
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.core.redis import redis_client
from app.services.workflow.workflow_queue import WorkflowQueueService, WorkflowJob
from app.services.workflow.workflow_engine import WorkflowExecutionEngine
from app.services.workflow.workflow_telemetry import WorkflowTelemetry

logger = logging.getLogger("flowpilot.workflow.worker")

DEFAULT_LEASE_TIMEOUT_SECONDS = 60


class WorkflowWorker:
    """Distributed background worker executing queued multi-agent workflows with concurrency leasing and crash recovery."""

    _shared_local_locks: Dict[str, Dict[str, Any]] = {}

    def __init__(self, worker_id: Optional[str] = None, lease_seconds: int = DEFAULT_LEASE_TIMEOUT_SECONDS):
        self.worker_id = worker_id or f"worker-{os.getpid()}-{uuid.uuid4().hex[:6]}"
        self.lease_seconds = lease_seconds
        self.is_running = False
        self._shutdown_event = asyncio.Event()

    async def acquire_lease(self, workflow_id: str) -> bool:
        """Acquires a distributed execution lease/lock for the workflow to prevent concurrent duplicate execution."""
        lock_key = f"flowpilot:lock:workflow:{workflow_id}"

        # 1. Distributed Redis Lease Lock
        if redis_client.connected and redis_client.client:
            try:
                acquired = await redis_client.client.set(
                    lock_key,
                    self.worker_id,
                    ex=self.lease_seconds,
                    nx=True
                )
                if acquired:
                    logger.debug(f"Worker '{self.worker_id}' acquired Redis lease for workflow '{workflow_id}'.")
                    return True
                else:
                    current_owner = await redis_client.client.get(lock_key)
                    logger.warning(f"Workflow '{workflow_id}' lease held by '{current_owner}'. Contention detected.")
                    return False
            except Exception as e:
                logger.error(f"Redis lock acquisition error ({str(e)}). Falling back to local lock.")

        # 2. Local fallback lock for test / disconnected mode
        now = time.time()
        lock_info = WorkflowWorker._shared_local_locks.get(workflow_id)
        if lock_info and lock_info.get("expires_at", 0) > now and lock_info.get("owner") != self.worker_id:
            return False  # Held by another worker
        WorkflowWorker._shared_local_locks[workflow_id] = {"owner": self.worker_id, "expires_at": now + self.lease_seconds}
        return True

    async def release_lease(self, workflow_id: str):
        """Releases the execution lease after completing or safely pausing the workflow."""
        lock_key = f"flowpilot:lock:workflow:{workflow_id}"

        if redis_client.connected and redis_client.client:
            try:
                # Release only if owned by this worker
                val = await redis_client.client.get(lock_key)
                if val == self.worker_id:
                    await redis_client.client.delete(lock_key)
                    logger.debug(f"Worker '{self.worker_id}' released Redis lease for workflow '{workflow_id}'.")
            except Exception as e:
                logger.error(f"Redis lock release error ({str(e)})")

        lock_info = WorkflowWorker._shared_local_locks.get(workflow_id)
        if lock_info and lock_info.get("owner") == self.worker_id:
            WorkflowWorker._shared_local_locks.pop(workflow_id, None)

    async def process_job(self, job: WorkflowJob) -> bool:
        """Executes a single dequeued workflow job with full database session and lifecycle management."""
        wf_id = job.workflow_id
        user_id = job.user_id

        # 1. Acquire distributed lease
        locked = await self.acquire_lease(wf_id)
        if not locked:
            logger.warning(f"Worker '{self.worker_id}' could not acquire lease for workflow '{wf_id}'. Re-queuing with delay.")
            await WorkflowQueueService.retry(job, delay_seconds=2.0)
            return False

        try:
            async with AsyncSessionLocal() as db:
                if job.action == "resume" and job.approval_id and job.approval_decision:
                    logger.info(f"Worker '{self.worker_id}' resuming approved workflow '{wf_id}' (Approval: {job.approval_id}).")
                    await WorkflowExecutionEngine.process_approval(
                        workflow_id=wf_id,
                        approval_id=job.approval_id,
                        decision=job.approval_decision,
                        user_id=user_id,
                        reason=job.approval_reason,
                        db=db
                    )
                else:
                    logger.info(f"Worker '{self.worker_id}' executing DAG workflow '{wf_id}' for user '{user_id}'.")
                    await WorkflowExecutionEngine.execute_graph(
                        workflow_id=wf_id,
                        user_id=user_id,
                        db=db
                    )

            await WorkflowQueueService.ack(job)
            return True
        except Exception as e:
            logger.error(f"Worker execution failed for workflow '{wf_id}': {str(e)}", exc_info=True)
            await WorkflowQueueService.retry(job, delay_seconds=2.0)
            return False
        finally:
            await self.release_lease(wf_id)

    async def run_once(self, timeout_seconds: float = 1.0) -> bool:
        """Pulls and executes one job if available."""
        job = await WorkflowQueueService.dequeue(timeout_seconds=timeout_seconds)
        if not job:
            return False
        return await self.process_job(job)

    async def start(self):
        """Starts continuous worker execution loop."""
        self.is_running = True
        logger.info(f"Workflow Worker '{self.worker_id}' started. Listening for jobs...")

        while self.is_running and not self._shutdown_event.is_set():
            try:
                await self.run_once(timeout_seconds=1.0)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Worker loop error: {str(e)}")
                await asyncio.sleep(1.0)

        logger.info(f"Workflow Worker '{self.worker_id}' stopped gracefully.")

    def stop(self):
        """Triggers graceful worker shutdown."""
        self.is_running = False
        self._shutdown_event.set()


# Default singleton worker for in-process execution pool
default_worker = WorkflowWorker()


async def run_worker_cli():
    """Standalone CLI entry point for running a worker process."""
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    worker = WorkflowWorker()

    def handle_signal(sig, frame):
        logger.info(f"Signal {sig} received. Initiating graceful worker shutdown...")
        worker.stop()

    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    # Initialize redis and run worker
    await redis_client.init_redis()
    await worker.start()


if __name__ == "__main__":
    asyncio.run(run_worker_cli())
