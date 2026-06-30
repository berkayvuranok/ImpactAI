"""Analysis pipeline Celery tasks."""

from __future__ import annotations

import asyncio

from code_impact.application.services.graph_build_service import GraphBuildService
from code_impact.application.services.repository_sync_service import RepositorySyncService
from code_impact.infrastructure.config.logging import get_logger
from code_impact.infrastructure.config.settings import get_settings
from code_impact.infrastructure.persistence.database import create_session_factory
from code_impact.infrastructure.persistence.repositories import (
    SqlAlchemyCommitRepository,
    SqlAlchemyGraphRepository,
    SqlAlchemyRepositoryRepository,
    SqlAlchemySyncJobRepository,
)
from code_impact.infrastructure.queue.celery_app import celery_app
from code_impact.infrastructure.git.git_service import GitService
from code_impact.infrastructure.graph.dependency_graph_builder import DependencyGraphBuilder
from code_impact.infrastructure.graph.graph_storage import GraphStorage

logger = get_logger(__name__)


async def _run_sync_async(
    repository_id: str,
    job_id: str,
    full_sync: bool,
    since_sha: str | None,
) -> dict:
    from uuid import UUID

    settings = get_settings()
    session_factory = create_session_factory(settings)

    async with session_factory() as session:
        git_service = GitService(settings.git_storage_path, settings.max_repo_size_mb)
        sync_service = RepositorySyncService(
            git_service=git_service,
            repository_repo=SqlAlchemyRepositoryRepository(session),
            commit_repo=SqlAlchemyCommitRepository(session),
            sync_job_repo=SqlAlchemySyncJobRepository(session),
        )
        job = await sync_service.run_sync(
            repository_id=UUID(repository_id),
            job_id=UUID(job_id),
            full_sync=full_sync,
            since_sha=since_sha,
        )
        await session.commit()

        if job.status.value == "completed" and job.stats.get("head_sha"):
            build_graph_task.delay(repository_id, job.stats["head_sha"])

        return {"status": job.status.value, "stats": job.stats}


async def _run_build_graph_async(repository_id: str, commit_sha: str) -> dict:
    from uuid import UUID

    settings = get_settings()
    session_factory = create_session_factory(settings)

    async with session_factory() as session:
        git_service = GitService(settings.git_storage_path, settings.max_repo_size_mb)
        service = GraphBuildService(
            graph_builder=DependencyGraphBuilder(git_service),
            graph_repo=SqlAlchemyGraphRepository(session),
            repository_repo=SqlAlchemyRepositoryRepository(session),
            graph_storage=GraphStorage(settings.graph_storage_path),
        )
        snapshot = await service.build_and_persist(UUID(repository_id), commit_sha)
        await session.commit()

        from code_impact.infrastructure.queue.tasks.embedding import index_embeddings_task

        index_embeddings_task.delay(repository_id, False, True)

        return {
            "status": "completed",
            "commit_sha": snapshot.commit_sha,
            "node_count": snapshot.node_count,
            "edge_count": snapshot.edge_count,
        }


@celery_app.task(name="analysis.sync_repository", bind=True, max_retries=3)
def sync_repository_task(
    self,
    repository_id: str,
    job_id: str,
    full_sync: bool = False,
    since_sha: str | None = None,
) -> dict:
    """Clone/pull repository and index commits."""
    try:
        return asyncio.run(_run_sync_async(repository_id, job_id, full_sync, since_sha))
    except Exception as exc:
        logger.exception("sync_repository_task_failed", repository_id=repository_id)
        raise self.retry(exc=exc, countdown=30) from exc


@celery_app.task(name="analysis.build_graph", bind=True, max_retries=3)
def build_graph_task(self, repository_id: str, commit_sha: str) -> dict:
    """Build dependency graph at given commit."""
    try:
        return asyncio.run(_run_build_graph_async(repository_id, commit_sha))
    except Exception as exc:
        logger.exception("build_graph_task_failed", repository_id=repository_id)
        raise self.retry(exc=exc, countdown=30) from exc
