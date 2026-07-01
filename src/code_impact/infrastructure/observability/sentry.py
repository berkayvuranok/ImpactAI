"""Optional Sentry error tracking — no-op if unconfigured or package missing."""

from __future__ import annotations

import structlog

from code_impact.infrastructure.config.settings import Settings

logger = structlog.get_logger(__name__)


def init_sentry(settings: Settings) -> None:
    if not settings.sentry_dsn:
        return
    try:
        import sentry_sdk
        from sentry_sdk.integrations.fastapi import FastApiIntegration
    except ImportError:
        logger.warning("sentry_not_installed", hint="pip install sentry-sdk[fastapi]")
        return

    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        environment=settings.app_env,
        traces_sample_rate=settings.sentry_traces_sample_rate,
        integrations=[FastApiIntegration()],
    )
    logger.info("sentry_initialized", environment=settings.app_env)
