import os
import time
import uuid
import asyncio
import logging
import signal
from typing import Optional, Dict, Any, Set, Tuple
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.core.redis import redis_client
from app.services.workflow.workflow_queue import WorkflowQueueService, WorkflowJob
from app.services.workflow.workflow_engine import WorkflowExecutionEngine
from app.services.workflow.workflow_telemetry import WorkflowTelemetry

logger = logging.getLogger("flowpilot.workflow.worker")

DEFAULT_LEASE_TIMEOUT_SECONDS = 30
DEFAULT_HEARTBEAT_INTERVAL_SECONDS = 10


class WorkflowWorker:
    """Distributed background worker executing queued workflows with heartbeat renewal, fencing tokens, and crash recovery."""

    # In-memory shared lock table for local/test execution mode
    _shared_local_locks: Dict[str, Dict[str, Any]] = {}
    _local_fencing_counters: Dict[str, int] = {}

    def __init__(self, worker_id: Optional[str] = None, lease_seconds: int = DEFAULT_LEASE_TIMEOUT_SECONDS):
        self.worker_id = worker_id or f"worker-{os.getpid()}-{uuid.uuid4().hex[:6]}"
        self.lease_seconds = lease_seconds
        self.heartbeat_interval = max(1.0, lease_seconds / 3.0)
        self.is_running = False
        self._shutdown_event = asyncio.Event()
        self._active_heartbeats: Dict[str, asyncio.Task] = {}
        self._lost_leases: Set[str] = set()

    async def acquire_lease(self, workflow_id: str) -> Tuple[bool, Optional[int]]:
        """Acquires a distributed execution lease and generates an incremental fencing token."""
        lock_key = f"flowpilot:lock:workflow:{workflow_id}"
        fence_key = f"flowpilot:fence:workflow:{workflow_id}"

        # 1. Distributed Redis Lease Lock
        if redis_client.connected and redis_client.client:
            try:
                # Increment fencing token
                fencing_token = await redis_client.client.incr(fence_key)
                lock_val = f"{self.worker_id}:{fencing_token}"

                acquired = await redis_client.client.set(
                    lock_key,
                    lock_val,
                    ex=self.lease_seconds,
                    nx=True
                )
                if acquired:
                    self._lost_leases.discard(workflow_id)
                    WorkflowTelemetry.record_lease_acquired(workflow_id, self.worker_id)
                    logger.debug(f"Worker '{self.worker_id}' acquired Redis lease for workflow '{workflow_id}' (Fence: {fencing_token}).")
                    return True, fencing_token
                else:
                    current_owner = await redis_client.client.get(lock_key)
                    WorkflowTelemetry.record_lease_failed(workflow_id, self.worker_id, "Contention")
                    logger.warning(f"Workflow '{workflow_id}' lease held by '{current_owner}'. Contention detected.")
                    return False, None
            except Exception as e:
                logger.error(f"Redis lease acquisition error ({str(e)}). Falling back to local lock.")

        # 2. Local fallback lock for test / disconnected mode
        now = time.time()
        lock_info = WorkflowWorker._shared_local_locks.get(workflow_id)
        if lock_info and lock_info.get("expires_at", 0) > now and lock_info.get("owner") != self.worker_id:
            WorkflowTelemetry.record_lease_failed(workflow_id, self.worker_id, "Local Contention")
            return False, None

        current_fence = WorkflowWorker._local_fencing_counters.get(workflow_id, 0) + 1
        WorkflowWorker._local_fencing_counters[workflow_id] = current_fence
        WorkflowWorker._shared_local_locks[workflow_id] = {
            "owner": self.worker_id,
            "fencing_token": current_fence,
            "expires_at": now + self.lease_seconds
        }
        self._lost_leases.discard(workflow_id)
        WorkflowTelemetry.record_lease_acquired(workflow_id, self.worker_id)
        return True, current_fence

    async def renew_lease(self, workflow_id: str, fencing_token: int) -> bool:
        """Renews an active distributed lease before expiration if still owned by this worker."""
        lock_key = f"flowpilot:lock:workflow:{workflow_id}"
        expected_val = f"{self.worker_id}:{fencing_token}"

        if redis_client.connected and redis_client.client:
            try:
                # Atomically renew only if value matches expected worker and fencing token
                val = await redis_client.client.get(lock_key)
                if val == expected_val:
                    await redis_client.client.expire(lock_key, self.lease_seconds)
                    WorkflowTelemetry.record_lease_renewed(workflow_id, self.worker_id)
                    logger.debug(f"Worker '{self.worker_id}' renewed Redis lease for workflow '{workflow_id}'.")
                    return True
                else:
                    logger.error(f"Lease renewal failed for workflow '{workflow_id}': Stale worker detected (current owner: '{val}').")
                    self._lost_leases.add(workflow_id)
                    WorkflowTelemetry.record_stale_worker_fenced(workflow_id, self.worker_id)
                    return False
            except Exception as e:
                logger.error(f"Redis lease renewal error: {str(e)}")
                return False

        # Local lock renewal
        now = time.time()
        lock_info = WorkflowWorker._shared_local_locks.get(workflow_id)
        if lock_info and lock_info.get("owner") == self.worker_id and lock_info.get("fencing_token") == fencing_token:
            lock_info["expires_at"] = now + self.lease_seconds
            WorkflowTelemetry.record_lease_renewed(workflow_id, self.worker_id)
            return True

        self._lost_leases.add(workflow_id)
        WorkflowTelemetry.record_stale_worker_fenced(workflow_id, self.worker_id)
        return False

    async def verify_lease_ownership(self, workflow_id: str, fencing_token: int) -> bool:
        """Verifies if this worker currently holds an unexpired, unfenced lease for the workflow."""
        if workflow_id in self._lost_leases:
            return False

        lock_key = f"flowpilot:lock:workflow:{workflow_id}"
        expected_val = f"{self.worker_id}:{fencing_token}"

        if redis_client.connected and redis_client.client:
            try:
                val = await redis_client.client.get(lock_key)
                return val == expected_val
            except Exception:
                return False

        now = time.time()
        lock_info = WorkflowWorker._shared_local_locks.get(workflow_id)
        if not lock_info:
            return False
        return (
            lock_info.get("owner") == self.worker_id
            and lock_info.get("fencing_token") == fencing_token
            and lock_info.get("expires_at", 0) > now
        )

    async def _heartbeat_loop(self, workflow_id: str, fencing_token: int, stop_event: asyncio.Event):
        """Continuous background task renewing lease periodically until execution completes or lease is lost."""
        while not stop_event.is_set() and not self._shutdown_event.is_set():
            try:
                await asyncio.wait_for(stop_event.wait(), timeout=self.heartbeat_interval)
                break  # Stop requested
            except asyncio.TimeoutError:
                pass

            if stop_event.is_set():
                break

            renewed = await self.renew_lease(workflow_id, fencing_token)
            if not renewed:
                logger.error(f"Heartbeat lost lease for workflow '{workflow_id}'. Aborting further steps.")
                self._lost_leases.add(workflow_id)
                break

    async def release_lease(self, workflow_id: str, fencing_token: Optional[int] = None):
        """Releases the execution lease cleanly after workflow finishes or safely pauses."""
        # Stop background heartbeat
        hb_task = self._active_heartbeats.pop(workflow_id, None)
        if hb_task and not hb_task.done():
            hb_task.cancel()

        lock_key = f"flowpilot:lock:workflow:{workflow_id}"
        expected_val = f"{self.worker_id}:{fencing_token}" if fencing_token else None

        if redis_client.connected and redis_client.client:
            try:
                val = await redis_client.client.get(lock_key)
                if expected_val is None or val == expected_val:
                    await redis_client.client.delete(lock_key)
                    logger.debug(f"Worker '{self.worker_id}' released Redis lease for workflow '{workflow_id}'.")
            except Exception as e:
                logger.error(f"Redis lock release error ({str(e)})")

        lock_info = WorkflowWorker._shared_local_locks.get(workflow_id)
        if lock_info and lock_info.get("owner") == self.worker_id:
            WorkflowWorker._shared_local_locks.pop(workflow_id, None)

        self._lost_leases.discard(workflow_id)

    async def process_job(self, job: WorkflowJob) -> bool:
        """Executes a single dequeued workflow job with full lease heartbeat and fencing verification."""
        wf_id = job.workflow_id
        user_id = job.user_id

        # 1. Acquire distributed lease & fencing token
        locked, fencing_token = await self.acquire_lease(wf_id)
        if not locked or fencing_token is None:
            logger.warning(f"Worker '{self.worker_id}' could not acquire lease for workflow '{wf_id}'. Re-queuing with delay.")
            await WorkflowQueueService.retry(job, delay_seconds=2.0)
            return False

        # 2. Start background heartbeat renewal
        stop_heartbeat = asyncio.Event()
        hb_task = asyncio.create_task(self._heartbeat_loop(wf_id, fencing_token, stop_heartbeat))
        self._active_heartbeats[wf_id] = hb_task

        async def lease_verifier() -> bool:
            return await self.verify_lease_ownership(wf_id, fencing_token)

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
                        db=db,
                        lease_verifier=lease_verifier
                    )
                else:
                    logger.info(f"Worker '{self.worker_id}' executing DAG workflow '{wf_id}' for user '{user_id}'.")
                    await WorkflowExecutionEngine.execute_graph(
                        workflow_id=wf_id,
                        user_id=user_id,
                        db=db,
                        lease_verifier=lease_verifier
                    )

            # Check if lease was lost during execution before acknowledging
            if await lease_verifier():
                await WorkflowQueueService.ack(job)
                return True
            else:
                logger.error(f"Worker '{self.worker_id}' finished with lost lease for workflow '{wf_id}'. Not acknowledging job.")
                return False
        except Exception as e:
            logger.error(f"Worker execution failed for workflow '{wf_id}': {str(e)}", exc_info=True)
            await WorkflowQueueService.retry(job, delay_seconds=2.0)
            return False
        finally:
            stop_heartbeat.set()
            if hb_task and not hb_task.done():
                hb_task.cancel()
            await self.release_lease(wf_id, fencing_token)

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
        for wf_id, task in list(self._active_heartbeats.items()):
            if not task.done():
                task.cancel()


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
