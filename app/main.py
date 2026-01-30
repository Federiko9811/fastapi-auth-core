"""
FastAPI Auth Core Application.

A template API with JWT authentication using HttpOnly cookies.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.api.v1.router import api_router
from app.core.cache import close_redis
from app.core.config import settings
from app.core.logging import get_logger, setup_logging
from app.core.rate_limit import RateLimitMiddleware
from app.db.session import SessionLocal

# Initialize logging
setup_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan handler for startup and shutdown events."""
    # Startup
    logger.info(f"Starting {settings.PROJECT_NAME}")
    yield
    # Shutdown
    await close_redis()
    logger.info(f"Shutting down {settings.PROJECT_NAME}")


app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    version="1.0.0",
    lifespan=lifespan,
)

# Rate limiting middleware (must be added before CORS)
app.add_middleware(RateLimitMiddleware)

# Configure CORS middleware
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.BACKEND_CORS_ORIGINS,
        allow_credentials=True,  # Required for cookies
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Include all V1 routes with the prefix defined in settings (/api/v1)
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/")
async def root() -> dict:
    """
    Root endpoint - quick status check.

    Returns:
        Project name and status.
    """
    return {"status": "ok", "project": settings.PROJECT_NAME}


@app.get("/health")
async def health_check() -> dict:
    """
    Detailed health check endpoint.

    Checks database connectivity and returns system status.

    Returns:
        Health status including database connectivity.
    """
    health = {
        "status": "healthy",
        "project": settings.PROJECT_NAME,
        "version": "1.0.0",
        "database": "unknown",
    }

    # Check database connectivity
    try:
        async with SessionLocal() as session:
            await session.execute(text("SELECT 1"))
            health["database"] = "connected"
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        health["status"] = "unhealthy"
        health["database"] = f"error: {str(e)}"

    return health
