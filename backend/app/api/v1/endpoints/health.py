from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import time
from app.core.database import get_db
from app.core.redis import redis_service
from app.core.config import settings

router = APIRouter()


@router.get("")
async def global_health_check(db: AsyncSession = Depends(get_db)):
    """Liveness probe: Returns HTTP 200 when service process is running."""
    return {
        "status": "active",
        "service": settings.PROJECT_NAME,
        "environment": settings.ENVIRONMENT,
        "version": "1.0.0"
    }


@router.get("/ready")
async def readiness_check(db: AsyncSession = Depends(get_db)):
    """Readiness probe: Validates active database and Redis cache connections."""
    db_connected = False
    try:
        await db.execute(text("SELECT 1"))
        db_connected = True
    except Exception:
        db_connected = False

    redis_health = await redis_service.check_health()
    redis_connected = redis_health.get("connected", False)

    is_ready = db_connected  # DB connection is mandatory for readiness

    if not is_ready:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "status": "not_ready",
                "database": "connected" if db_connected else "disconnected",
                "redis": "connected" if redis_connected else "disconnected"
            }
        )

    return {
        "status": "ready",
        "database": "connected",
        "redis": "connected" if redis_connected else "disconnected (fail-safe fallback)",
        "worker": "active"
    }


@router.get("/version")
async def version_check():
    """Version probe: Returns application release metadata and build details."""
    return {
        "name": settings.PROJECT_NAME,
        "version": "1.0.0",
        "buildSha": "release-v1.0.0-prod",
        "environment": settings.ENVIRONMENT
    }


@router.get("/database")
async def database_health_check(db: AsyncSession = Depends(get_db)):
    """Granular PostgreSQL database health & query latency diagnostic."""
    start_time = time.time()
    try:
        res = await db.execute(text("SELECT 1"))
        res.scalar()
        latency_ms = round((time.time() - start_time) * 1000, 2)
        return {
            "status": "ok",
            "database": "PostgreSQL",
            "connected": True,
            "latencyMs": latency_ms,
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "status": "error",
                "database": "PostgreSQL",
                "connected": False,
                "error": str(e),
            }
        )


@router.get("/redis")
async def redis_health_check():
    """Granular Redis cache & event bus health diagnostic."""
    health_info = await redis_service.check_health()
    if not health_info.get("connected"):
        return {
            "status": "degraded",
            "redis": "unavailable",
            "mode": "fail-safe fallback",
            "message": "Redis disconnected. Application operating normally via fallback."
        }
    return health_info
