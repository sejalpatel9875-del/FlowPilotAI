import logging
from typing import Optional, Any
from app.core.config import settings

logger = logging.getLogger("flowpilot.redis")


class RedisService:
    def __init__(self):
        self.connected = False
        self.client = None

    async def init_redis(self):
        """Initializes Redis async connection gracefully."""
        try:
            import redis.asyncio as aioredis
            self.client = aioredis.from_url(
                settings.REDIS_URL,
                encoding="utf8",
                decode_responses=True,
                socket_timeout=2.0,
                socket_connect_timeout=2.0,
            )
            await self.client.ping()
            self.connected = True
            logger.info("Connected to Redis cache instance.")
        except Exception as e:
            self.connected = False
            logger.warning(f"Redis unavailable ({str(e)}). Operating in fail-safe fallback mode.")

    async def get(self, key: str) -> Optional[str]:
        """Fail-safe key retrieval."""
        if not self.connected or not self.client:
            return None
        try:
            return await self.client.get(key)
        except Exception as e:
            logger.error(f"Redis GET failed for key '{key}': {str(e)}")
            return None

    async def set(self, key: str, value: str, expire_seconds: int = 3600) -> bool:
        """Fail-safe key storage."""
        if not self.connected or not self.client:
            return False
        try:
            await self.client.set(key, value, ex=expire_seconds)
            return True
        except Exception as e:
            logger.error(f"Redis SET failed for key '{key}': {str(e)}")
            return False

    async def delete(self, key: str) -> bool:
        """Fail-safe key deletion."""
        if not self.connected or not self.client:
            return False
        try:
            await self.client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Redis DELETE failed for key '{key}': {str(e)}")
            return False

    async def is_rate_limited(self, key: str, max_requests: int = 60, window_seconds: int = 60) -> bool:
        """
        Fail-safe sliding window rate limiter.
        If Redis is down, fails open (returns False) so user operations are never blocked.
        """
        if not self.connected or not self.client:
            return False  # Fail-safe open mode

        rate_key = f"rate_limit:{key}"
        try:
            current_count = await self.client.incr(rate_key)
            if current_count == 1:
                await self.client.expire(rate_key, window_seconds)

            if current_count > max_requests:
                return True
            return False
        except Exception as e:
            logger.error(f"Redis rate limiting check failed for key '{key}': {str(e)}")
            return False  # Fail-safe open mode

    async def check_health(self) -> dict:
        """Returns diagnostic state for health check endpoint."""
        if not self.connected or not self.client:
            return {
                "status": "unavailable",
                "connected": False,
                "mode": "fail-safe fallback",
                "details": "Redis server disconnected or unreachable."
            }
        try:
            await self.client.ping()
            info = await self.client.info("memory")
            used_memory = info.get("used_memory_human", "unknown")
            return {
                "status": "ok",
                "connected": True,
                "mode": "active",
                "usedMemory": used_memory,
            }
        except Exception as e:
            self.connected = False
            return {
                "status": "error",
                "connected": False,
                "mode": "fail-safe fallback",
                "details": str(e),
            }


# Global singleton Redis service instance
redis_service = RedisService()
# Backward compatibility alias
redis_client = redis_service
