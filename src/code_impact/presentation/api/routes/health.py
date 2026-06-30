"""Health check endpoints."""

from fastapi import APIRouter, Request

from code_impact.application.schemas import HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check(request: Request) -> HealthResponse:
    settings = request.app.state.settings
    return HealthResponse(
        status="healthy",
        version="0.1.0",
        environment=settings.app_env,
    )


@router.get("/health/ready")
async def readiness_check() -> dict:
    # Step 2+ will add DB/Redis/Qdrant connectivity checks
    return {"status": "ready", "checks": {"database": "pending", "redis": "pending"}}
