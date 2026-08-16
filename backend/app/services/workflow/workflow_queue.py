import json
import time
import uuid
import asyncio
import logging
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field

from app.core.redis import redis_client

logger = logging.getLogger("flowpilot.workflow.queue")

QUEUE_NAME = "flowpilot:workflow:queue"
PROCESSING_QUEUE_NAME = "flowpilot:workflow:processing"
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
    payload: Dict[str, Any] = Field(default_factory=dict)


class WorkflowQueueService:
    """Durable Redis-backed job queue for asynchronous multi-agent workflow execution with fail-safe fallback."""

    _in_memory_queue: asyncio.Queue = asyncio.Queue()
    _in_memory_processing: Dict[str, WorkflowJob] = {}

    @classmethod
    async def enqueue(cls, job: WorkflowJob) -> bool:
        """Pushes a workflow execution job into the queue."""
        job_json = job.model_dump_json()

        if redis_client.connected and redis_client.client:
            try:
                await redis_client.client.lpush(QUEUE_NAME, job_json)
                logger.info(f"Workflow job '{job.job_id}' (WF: {job.workflow_id}) enqueued to Redis.")
                return True
            except Exception as e:
                logger.error(f"Redis enqueue failed ({str(e)}). Falling back to in-memory queue.")

        # In-memory fail-safe queue
        await cls._in_memory_queue.put(job)
        logger.info(f"Workflow job '{job.job_id}' (WF: {job.workflow_id}) enqueued in-memory.")
        return True

    @classmethod
    async def dequeue(cls, timeout_seconds: float = 1.0) -> Optional[WorkflowJob]:
        """Pops a job from the queue into processing state with reliable delivery."""
        if redis_client.connected and redis_client.client:
            try:
                raw_job = await redis_client.client.brpoplpush(
                    QUEUE_NAME,
                    PROCESSING_QUEUE_NAME,
                    timeout=int(max(1, timeout_seconds))
                )
                if raw_job:
                    parsed = json.loads(raw_job)
                    return WorkflowJob(**parsed)
            except Exception as e:
                logger.error(f"Redis dequeue error ({str(e)}). Checking in-memory queue.")

        # In-memory queue dequeue
        try:
            job = await asyncio.wait_for(cls._in_memory_queue.get(), timeout=timeout_seconds)
            cls._in_memory_processing[job.job_id] = job
            return job
        except asyncio.TimeoutError:
            return None

    @classmethod
    async def ack(cls, job: WorkflowJob) -> bool:
        """Acknowledges successful processing of a workflow job, removing it from processing queue."""
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
        """Retries a failed job with bounded retry limit."""
        if job.retry_count >= MAX_JOB_RETRIES:
            logger.error(f"Job '{job.job_id}' for workflow '{job.workflow_id}' exceeded max retries ({MAX_JOB_RETRIES}). Dropping job.")
            await cls.ack(job)
            return False

        job.retry_count += 1
        await cls.ack(job)

        if delay_seconds > 0:
            await asyncio.sleep(delay_seconds)

        return await cls.enqueue(job)

    @classmethod
    async def get_queue_depth(cls) -> int:
        """Returns the count of pending workflow jobs in the queue."""
        if redis_client.connected and redis_client.client:
            try:
                return await redis_client.client.llen(QUEUE_NAME)
            except Exception:
                pass
        return cls._in_memory_queue.qsize()

    @classmethod
    async def clear_all(cls):
        """Clears test queues (used in unit tests)."""
        if redis_client.connected and redis_client.client:
            try:
                await redis_client.client.delete(QUEUE_NAME)
                await redis_client.client.delete(PROCESSING_QUEUE_NAME)
            except Exception:
                pass
        while not cls._in_memory_queue.empty():
            try:
                cls._in_memory_queue.get_nowait()
            except Exception:
                break
        cls._in_memory_processing.clear()
