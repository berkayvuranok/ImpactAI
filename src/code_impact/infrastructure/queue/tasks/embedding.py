"""Embedding indexing Celery tasks."""

from __future__ import annotations

import asyncio

from code_impact.application.services.embedding_index_service import EmbeddingIndexService
from code_impact.infrastructure.config.logging import get_logger
from code_impact.infrastructure.config.settings import get_settings
from code_impact.infrastructure.embeddings.mock_embedding_service import MockEmbeddingService
from code_impact.infrastructure.embeddings.sentence_transformer_service import (
    SentenceTransformerEmbeddingService,
)
from code_impact.infrastructure.git.git_service import GitService
from code_impact.infrastructure.persistence.database import create_session_factory
from code_impact.infrastructure.persistence.repositories import (
    SqlAlchemyCommitRepository,
    SqlAlchemyEmbeddingRepository,
    SqlAlchemyIssueRepository,
)
from code_impact.infrastructure.queue.celery_app import celery_app
from code_impact.infrastructure.vector.qdrant_store import QdrantVectorStore

logger = get_logger(__name__)


def _embedding_service(settings):
    if settings.embedding_backend == "mock":
        return MockEmbeddingService()
    return SentenceTransformerEmbeddingService(settings.embedding_model)


async def _run_index_embeddings_async(
    repository_id: str,
    reindex: bool,
    include_issues: bool,
) -> dict:
    from uuid import UUID

    settings = get_settings()
    session_factory = create_session_factory(settings)

    async with session_factory() as session:
        git_service = GitService(settings.git_storage_path, settings.max_repo_size_mb)
        service = EmbeddingIndexService(
            embedding_service=_embedding_service(settings),
            vector_store=QdrantVectorStore(settings.qdrant_host, settings.qdrant_port),
            embedding_repo=SqlAlchemyEmbeddingRepository(session),
            commit_repo=SqlAlchemyCommitRepository(session),
            issue_repo=SqlAlchemyIssueRepository(session),
            git_service=git_service,
            settings=settings,
        )
        commit_stats = await service.index_repository_commits(
            UUID(repository_id), reindex=reindex
        )
        issue_stats = {"indexed": 0, "skipped": 0, "total": 0}
        if include_issues:
            issue_stats = await service.index_repository_issues(
                UUID(repository_id), reindex=reindex
            )
        await session.commit()
        return {"commits": commit_stats, "issues": issue_stats}


@celery_app.task(name="embedding.index_repository", bind=True, max_retries=3)
def index_embeddings_task(
    self,
    repository_id: str,
    reindex: bool = False,
    include_issues: bool = True,
) -> dict:
    """Index commit and issue embeddings into Qdrant."""
    try:
        return asyncio.run(_run_index_embeddings_async(repository_id, reindex, include_issues))
    except Exception as exc:
        logger.exception("index_embeddings_task_failed", repository_id=repository_id)
        raise self.retry(exc=exc, countdown=30) from exc
