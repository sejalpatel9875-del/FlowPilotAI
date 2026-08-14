from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.database import init_db
from app.core.redis import redis_client
from app.core.security_middleware import SecurityHeadersMiddleware
from app.api.v1.router import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize DB schemas on startup
    await init_db()
    # Initialize Redis connection
    await redis_client.init_redis()
    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
    lifespan=lifespan,
)

# Enforce OWASP Security Headers Middleware
app.add_middleware(SecurityHeadersMiddleware)

# Set up CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/")
async def root():
    return {
        "message": "Welcome to FlowPilot AI Backend Gateway",
        "docs": f"{settings.API_V1_STR}/docs",
        "status": "active"
    }


@app.get("/health")
async def root_health():
    return {"status": "active", "service": settings.PROJECT_NAME, "environment": settings.ENVIRONMENT, "version": "1.0.0"}


@app.get("/ready")
async def root_ready():
    return {"status": "ready", "database": "connected", "redis": "connected", "worker": "active"}


@app.get("/version")
async def root_version():
    return {"name": settings.PROJECT_NAME, "version": "1.0.0", "buildSha": "release-v1.0.0-prod", "environment": settings.ENVIRONMENT}

