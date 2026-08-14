import pytest
from app.core.redis import RedisService

@pytest.mark.asyncio
async def test_redis_failsafe_when_disconnected():
    # Test Redis service when connection is intentionally offline
    service = RedisService()
    service.connected = False
    service.client = None

    # Get should return None without throwing an exception
    val = await service.get("test_key")
    assert val is None

    # Set should return False without throwing an exception
    set_success = await service.set("test_key", "test_value")
    assert set_success is False

    # Delete should return False without throwing an exception
    del_success = await service.delete("test_key")
    assert del_success is False

    # Rate limiter should fail-safe open (return False) so users are not blocked
    is_limited = await service.is_rate_limited("user_123", max_requests=5, window_seconds=60)
    assert is_limited is False

    # Health check returns fail-safe mode info
    health = await service.check_health()
    assert health["connected"] == False
    assert health["mode"] == "fail-safe fallback"
