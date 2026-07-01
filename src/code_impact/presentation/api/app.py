"""FastAPI application factory."""

from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator

from code_impact.infrastructure.config.logging import setup_logging
from code_impact.infrastructure.config.settings import Settings, get_settings
from code_impact.infrastructure.persistence.bootstrap import ensure_system_user
from code_impact.infrastructure.persistence.database import create_session_factory
from code_impact.presentation.api.routes import analysis, auth, embeddings, graph, health, predictions, repositories, search, webhooks
from code_impact.presentation.api.exception_handlers import register_exception_handlers


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    settings: Settings = app.state.settings
    setup_logging(settings)

    session_factory = create_session_factory(settings)
    app.state.session_factory = session_factory

    if not getattr(app.state, "skip_bootstrap", False):
        async with session_factory() as session:
            try:
                await ensure_system_user(session)
            except Exception:
                await session.rollback()

    yield


def create_app(settings: Settings | None = None, *, skip_bootstrap: bool = False) -> FastAPI:
    settings = settings or get_settings()

    app = FastAPI(
        title="Code Impact Predictor AI",
        description="Production-grade AI system for predicting source code change impact",
        version="0.1.0",
        docs_url=f"{settings.api_prefix}/docs",
        redoc_url=f"{settings.api_prefix}/redoc",
        openapi_url=f"{settings.api_prefix}/openapi.json",
        lifespan=lifespan,
    )

    app.state.settings = settings
    app.state.skip_bootstrap = skip_bootstrap

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"] if settings.debug else [],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    prefix = settings.api_prefix
    register_exception_handlers(app)
    app.include_router(health.router, prefix=prefix, tags=["Health"])
    app.include_router(auth.router, prefix=prefix, tags=["Auth"])
    app.include_router(repositories.router, prefix=prefix, tags=["Repositories"])
    app.include_router(predictions.router, prefix=prefix, tags=["Predictions"])
    app.include_router(analysis.router, prefix=prefix, tags=["Analysis"])
    app.include_router(graph.router, prefix=prefix, tags=["Graph"])
    app.include_router(embeddings.router, prefix=prefix, tags=["Embeddings"])
    app.include_router(search.router, prefix=prefix, tags=["Search"])
    app.include_router(webhooks.router, prefix=prefix, tags=["Webhooks"])

    if settings.prometheus_enabled:
        Instrumentator().instrument(app).expose(app, endpoint="/metrics")

    return app
