"""Repository synchronization orchestration."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

from code_impact.domain.entities import Commit, Repository, SyncJob
from code_impact.domain.exceptions import EntityNotFoundError, RepositorySyncError
from code_impact.domain.repositories import (
    ICommitRepository,
    IRepositoryRepository,
    ISyncJobRepository,
)
from code_impact.domain.services.git_service import IGitService
from code_impact.infrastructure.config.logging import get_logger
from code_impact.infrastructure.git.git_service import is_rollback_commit

logger = get_logger(__name__)


class RepositorySyncService:
    """Clones/pulls a repo and indexes commits into PostgreSQL."""

    def __init__(
        self,
        git_service: IGitService,
        repository_repo: IRepositoryRepository,
        commit_repo: ICommitRepository,
        sync_job_repo: ISyncJobRepository,
    ) -> None:
        self._git = git_service
        self._repository_repo = repository_repo
        self._commit_repo = commit_repo
        self._sync_job_repo = sync_job_repo

    async def run_sync(
        self,
        repository_id: UUID,
        job_id: UUID,
        full_sync: bool = False,
        since_sha: str | None = None,
    ) -> SyncJob:
        job = await self._sync_job_repo.get_by_id(job_id)
        if not job:
            raise EntityNotFoundError("SyncJob", job_id)

        repository = await self._repository_repo.get_by_id(repository_id)
        if not repository:
            job.mark_failed(f"Repository not found: {repository_id}")
            await self._sync_job_repo.update(job)
            raise EntityNotFoundError("Repository", repository_id)

        job.mark_running()
        await self._sync_job_repo.update(job)

        try:
            clone_result = await self._git.clone_or_pull(
                repository_id=repository.id,
                url=repository.url,
                branch=repository.default_branch,
            )

            if full_sync:
                since_sha = None

            git_commits = await self._git.list_commits(
                repository_id=repository.id,
                branch=repository.default_branch,
                limit=1000,
                since_sha=since_sha,
            )

            domain_commits: list[Commit] = []
            for gc in git_commits:
                existing = await self._commit_repo.get_by_sha(repository.id, gc.sha)
                if existing:
                    continue
                domain_commits.append(
                    Commit(
                        id=uuid4(),
                        repository_id=repository.id,
                        sha=gc.sha,
                        message=gc.message,
                        author_email=gc.author_email,
                        committed_at=gc.committed_at,
                        is_rollback=is_rollback_commit(gc.message),
                        metadata={
                            "author_name": gc.author_name,
                            "parent_shas": gc.parent_shas,
                            "is_merge": gc.is_merge,
                        },
                    )
                )

            if domain_commits:
                await self._commit_repo.create_batch(domain_commits)

            repository.last_synced_at = datetime.now(UTC)
            await self._repository_repo.update(repository)

            stats = {
                "head_sha": clone_result.head_sha,
                "is_new_clone": clone_result.is_new_clone,
                "commits_indexed": len(domain_commits),
                "commits_scanned": len(git_commits),
            }
            job.mark_completed(stats)
            await self._sync_job_repo.update(job)

            logger.info(
                "repository_sync_complete",
                repository_id=str(repository_id),
                commits_indexed=len(domain_commits),
            )
            return job

        except (RepositorySyncError, Exception) as exc:
            logger.exception("repository_sync_failed", repository_id=str(repository_id))
            job.mark_failed(str(exc))
            await self._sync_job_repo.update(job)
            raise
