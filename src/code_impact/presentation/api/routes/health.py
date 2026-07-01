"""Health check endpoints — liveness and readiness."""

import asyncio

from fastapi import APIRouter, Request
from sqlalchemy import text

from code_impact.application.schemas import HealthResponse
from code_impact.infrastructure.config.settings import Settings

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check(request: Request) -> HealthResponse:
    """Liveness probe — process is up. Does not check dependencies."""
    settings = request.app.state.settings
    return HealthResponse(
        status="healthy",
        version="0.1.0",
        environment=settings.app_env,
    )


@router.get("/health/ready")
async def readiness_check(request: Request) -> dict:
    """Readiness probe — verifies database, Redis, and Qdrant connectivity."""
    settings = request.app.state.settings
    checks = {
        "database": await _check_database(request),
        "redis": await _check_redis(settings),
        "qdrant": await _check_qdrant(settings),
    }
    overall = "ready" if all(v == "ok" for v in checks.values()) else "degraded"
    return {"status": overall, "checks": checks}


async def _check_database(request: Request) -> str:
    try:
        session_factory = request.app.state.session_factory
        async with session_factory() as session:
            await session.execute(text("SELECT 1"))
        return "ok"
    except Exception as exc:  # noqa: BLE001
        return f"error: {exc}"


async def _check_redis(settings: Settings) -> str:
    try:
        import redis.asyncio as aioredis

        client = aioredis.from_url(str(settings.redis_url))
        try:
            await asyncio.wait_for(client.ping(), timeout=2.0)
        finally:
            await client.aclose()
        return "ok"
    except Exception as exc:  # noqa: BLE001
        return f"error: {exc}"


async def _check_qdrant(settings: Settings) -> str:
    try:
        import httpx

        url = f"http://{settings.qdrant_host}:{settings.qdrant_port}/readyz"
        async with httpx.AsyncClient(timeout=2.0) as client:
            response = await client.get(url)
            response.raise_for_status()
        return "ok"
    except Exception as exc:  # noqa: BLE001
        return f"error: {exc}"
