"""Celery application for async ML pipeline tasks."""

from celery import Celery

from code_impact.infrastructure.config.settings import get_settings

settings = get_settings()

celery_app = Celery(
    "code_impact",
    broker=str(settings.celery_broker_url),
    backend=str(settings.celery_result_backend),
    include=[
        "code_impact.infrastructure.queue.tasks.analysis",
        "code_impact.infrastructure.queue.tasks.prediction",
        "code_impact.infrastructure.queue.tasks.embedding",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_routes={
        "code_impact.infrastructure.queue.tasks.analysis.*": {"queue": "analysis"},
        "code_impact.infrastructure.queue.tasks.prediction.*": {"queue": "prediction"},
    },
    task_default_queue="analysis",
)
