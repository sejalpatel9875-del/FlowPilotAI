import json
import time
import uuid
import asyncio
import logging
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field

from app.core.config import settings
from app.core.redis import redis_client
from app.services.workflow.workflow_telemetry import WorkflowTelemetry

logger = logging.getLogger("flowpilot.workflow.queue")

QUEUE_NAME = "flowpilot:workflow:queue"
PROCESSING_QUEUE_NAME = "flowpilot:workflow:processing"
DLQ_NAME = "flowpilot:workflow:dlq"
MAX_JOB_RETRIES = 3


class WorkflowJob(BaseModel):
    job_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    workflow_id: str = Field(..., description="Target Workflow ID")
    user_id: str = Field(..., description="Tenant / User ID owner")
    action: str = Field("execute", description="'execute' or 'resume'")
    approval_id: Optional[str] = Field(None, description="Optional approval ID for resumed workflows")
    approval_decision: Optional[str] = Field(None, description="'approved' or 'rejected'")
    approval_reason: Optional[str] = Field(None, description="Reason provided during human review")
    retry_count: int = Field(0, description="Number of times job has been retried")
    enqueued_at: float = Field(default_factory=time.time)
    last_dequeued_at: Optional[float] = Field(None, description="Timestamp of last dequeue")
    payload: Dict[str, Any] = Field(default_factory=dict)


class WorkflowQueueService:
    """Durable Redis-backed job queue for asynchronous multi-agent workflow execution with DLQ and safe fallback."""

    _in_memory_queue: asyncio.Queue = asyncio.Queue()
    _in_memory_processing: Dict[str, WorkflowJob] = {}
    _in_memory_dlq: List[WorkflowJob] = []

    @classmethod
    async def enqueue(cls, job: WorkflowJob) -> bool:
        """Pushes a workflow execution job into the queue with production safety guard."""
        job_json = job.model_dump_json()

        # 1. Primary Redis Queue
        if redis_client.connected and redis_client.client:
            try:
                await redis_client.client.lpush(QUEUE_NAME, job_json)
                WorkflowTelemetry.record_job_enqueued(job.workflow_id, job.job_id)
                logger.info(f"Workflow job '{job.job_id}' (WF: {job.workflow_id}) enqueued to Redis.")
                return True
            except Exception as e:
                logger.error(f"Redis enqueue failed ({str(e)}).")

        # 2. Production Safety Guard: Do not silently store durable jobs in volatile memory in production
        if settings.ENVIRONMENT == "production":
            error_msg = f"Redis is unavailable: Cannot enqueue durable workflow job '{job.job_id}' in production."
            logger.critical(error_msg)
            raise RuntimeError(error_msg)

        # 3. Development / Test Fail-safe In-Memory Queue
        await cls._in_memory_queue.put(job)
        WorkflowTelemetry.record_job_enqueued(job.workflow_id, job.job_id)
        logger.info(f"Workflow job '{job.job_id}' (WF: {job.workflow_id}) enqueued in-memory (dev/test mode).")
        return True

    @classmethod
    async def dequeue(cls, timeout_seconds: float = 1.0) -> Optional[WorkflowJob]:
        """Pops a job from the queue into processing state with reliable delivery semantics."""
        if redis_client.connected and redis_client.client:
            try:
                raw_job = await redis_client.client.brpoplpush(
                    QUEUE_NAME,
                    PROCESSING_QUEUE_NAME,
                    timeout=int(max(1, timeout_seconds))
                )
                if raw_job:
                    parsed = json.loads(raw_job)
                    job = WorkflowJob(**parsed)
                    job.last_dequeued_at = time.time()
                    WorkflowTelemetry.record_job_dequeued(job.workflow_id, job.job_id)
                    return job
            except Exception as e:
                logger.error(f"Redis dequeue error ({str(e)}). Checking fallback queue.")

        # In-memory queue dequeue
        try:
            job = await asyncio.wait_for(cls._in_memory_queue.get(), timeout=timeout_seconds)
            job.last_dequeued_at = time.time()
            cls._in_memory_processing[job.job_id] = job
            WorkflowTelemetry.record_job_dequeued(job.workflow_id, job.job_id)
            return job
        except asyncio.TimeoutError:
            return None

    @classmethod
    async def ack(cls, job: WorkflowJob) -> bool:
        """Acknowledges successful processing of a workflow job, removing it from processing list."""
        if redis_client.connected and redis_client.client:
            try:
                raw_job = job.model_dump_json()
                await redis_client.client.lrem(PROCESSING_QUEUE_NAME, 1, raw_job)
                logger.debug(f"Workflow job '{job.job_id}' acknowledged in Redis.")
                return True
            except Exception as e:
                logger.error(f"Redis ack failed: {str(e)}")

        cls._in_memory_processing.pop(job.job_id, None)
        return True

    @classmethod
    async def retry(cls, job: WorkflowJob, delay_seconds: float = 1.0) -> bool:
        """Retries a failed job with bounded retry limit. Moves to Dead-Letter Queue (DLQ) if limit exceeded."""
        if job.retry_count >= MAX_JOB_RETRIES:
            logger.error(f"Job '{job.job_id}' (WF: {job.workflow_id}) exceeded max retries ({MAX_JOB_RETRIES}). Moving to Dead-Letter Queue (DLQ).")
            await cls._send_to_dlq(job)
            await cls.ack(job)
            return False

        job.retry_count += 1
        WorkflowTelemetry.record_job_retried(job.workflow_id, job.job_id, job.retry_count)
        await cls.ack(job)

        if delay_seconds > 0:
            await asyncio.sleep(delay_seconds)

        return await cls.enqueue(job)

    @classmethod
    async def _send_to_dlq(cls, job: WorkflowJob) -> bool:
        """Stores unrecoverable job into Dead-Letter Queue for operator visibility and audit."""
        WorkflowTelemetry.record_job_dlq(job.workflow_id, job.job_id, job.retry_count)
        job_json = job.model_dump_json()

        if redis_client.connected and redis_client.client:
            try:
                await redis_client.client.lpush(DLQ_NAME, job_json)
                logger.warning(f"Workflow job '{job.job_id}' persisted in Redis DLQ.")
                return True
            except Exception as e:
                logger.error(f"Failed to push to Redis DLQ: {str(e)}")

        cls._in_memory_dlq.append(job)
        return True

    @classmethod
    async def get_dlq_jobs(cls, limit: int = 50) -> List[WorkflowJob]:
        """Retrieves dead-letter queue entries for observability and manual operator inspection."""
        if redis_client.connected and redis_client.client:
            try:
                raw_items = await redis_client.client.lrange(DLQ_NAME, 0, limit - 1)
                return [WorkflowJob(**json.loads(r)) for r in raw_items]
            except Exception:
                pass
        return list(cls._in_memory_dlq[:limit])

    @classmethod
    async def get_queue_depth(cls) -> int:
        """Returns the count of pending workflow jobs in the main queue."""
        if redis_client.connected and redis_client.client:
            try:
                return await redis_client.client.llen(QUEUE_NAME)
            except Exception:
                pass
        return cls._in_memory_queue.qsize()

    @classmethod
    async def get_processing_count(cls) -> int:
        """Returns the count of jobs currently in processing state."""
        if redis_client.connected and redis_client.client:
            try:
                return await redis_client.client.llen(PROCESSING_QUEUE_NAME)
            except Exception:
                pass
        return len(cls._in_memory_processing)

    @classmethod
    async def get_dlq_depth(cls) -> int:
        """Returns the count of dead-letter jobs."""
        if redis_client.connected and redis_client.client:
            try:
                return await redis_client.client.llen(DLQ_NAME)
            except Exception:
                pass
        return len(cls._in_memory_dlq)

    @classmethod
    async def reclaim_stuck_processing_jobs(cls, max_idle_seconds: float = 120.0) -> int:
        """Scans processing queue and re-enqueues or recovers jobs whose workers died without acknowledging."""
        reclaimed_count = 0
        now = time.time()

        # In-memory processing list check
        stuck_job_ids = [
            jid for jid, j in cls._in_memory_processing.items()
            if (j.last_dequeued_at or 0) > 0 and (now - j.last_dequeued_at) > max_idle_seconds
        ]
        for jid in stuck_job_ids:
            job = cls._in_memory_processing.pop(jid, None)
            if job:
                logger.warning(f"Reclaiming stuck in-memory job '{jid}' (WF: {job.workflow_id}) after {max_idle_seconds}s idle.")
                await cls.retry(job, delay_seconds=0.1)
                reclaimed_count += 1

        return reclaimed_count

    @classmethod
    async def clear_all(cls):
        """Clears test queues and DLQs (used in test fixtures)."""
        if redis_client.connected and redis_client.client:
            try:
                await redis_client.client.delete(QUEUE_NAME)
                await redis_client.client.delete(PROCESSING_QUEUE_NAME)
                await redis_client.client.delete(DLQ_NAME)
            except Exception:
                pass
        while not cls._in_memory_queue.empty():
            try:
                cls._in_memory_queue.get_nowait()
            except Exception:
                break
        cls._in_memory_processing.clear()
        cls._in_memory_dlq.clear()
