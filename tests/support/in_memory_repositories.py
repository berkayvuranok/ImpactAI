"""In-memory repository implementations for testing."""

from uuid import UUID

from code_impact.domain.entities import Commit, Repository, SyncJob, User
from code_impact.domain.repositories import (
    ICommitRepository,
    IRepositoryRepository,
    ISyncJobRepository,
    IUserRepository,
)


class InMemoryUserRepository(IUserRepository):
    def __init__(self) -> None:
        self._store: dict[UUID, User] = {}

    async def get_by_id(self, user_id: UUID) -> User | None:
        return self._store.get(user_id)

    async def get_by_email(self, email: str) -> User | None:
        return next((u for u in self._store.values() if u.email == email), None)

    async def create(self, user: User) -> User:
        self._store[user.id] = user
        return user


class InMemoryRepositoryRepository(IRepositoryRepository):
    def __init__(self) -> None:
        self._store: dict[UUID, Repository] = {}

    async def get_by_id(self, repository_id: UUID) -> Repository | None:
        return self._store.get(repository_id)

    async def get_by_url(self, url: str) -> Repository | None:
        return next((r for r in self._store.values() if r.url == url), None)

    async def list_by_owner(self, owner_id: UUID) -> list[Repository]:
        return [r for r in self._store.values() if r.owner_id == owner_id]

    async def create(self, repository: Repository) -> Repository:
        self._store[repository.id] = repository
        return repository

    async def update(self, repository: Repository) -> Repository:
        self._store[repository.id] = repository
        return repository

    async def delete(self, repository_id: UUID) -> None:
        self._store.pop(repository_id, None)

    async def find_by_normalized_url(self, url: str) -> Repository | None:
        from code_impact.application.services.webhook_service import normalize_repo_url

        target = normalize_repo_url(url)
        for repo in self._store.values():
            if normalize_repo_url(repo.url) == target:
                return repo
        return None


class InMemoryCommitRepository(ICommitRepository):
    def __init__(self) -> None:
        self._store: list[Commit] = []

    async def get_by_sha(self, repository_id: UUID, sha: str) -> Commit | None:
        return next(
            (c for c in self._store if c.repository_id == repository_id and c.sha.startswith(sha)),
            None,
        )

    async def list_by_repository(
        self, repository_id: UUID, limit: int = 100, offset: int = 0
    ) -> list[Commit]:
        commits = [c for c in self._store if c.repository_id == repository_id]
        commits.sort(key=lambda c: c.committed_at, reverse=True)
        return commits[offset : offset + limit]

    async def create_batch(self, commits: list[Commit]) -> list[Commit]:
        self._store.extend(commits)
        return commits


class InMemorySyncJobRepository(ISyncJobRepository):
    def __init__(self) -> None:
        self._store: dict[UUID, SyncJob] = {}

    async def get_by_id(self, job_id: UUID) -> SyncJob | None:
        return self._store.get(job_id)

    async def create(self, job: SyncJob) -> SyncJob:
        self._store[job.id] = job
        return job

    async def update(self, job: SyncJob) -> SyncJob:
        self._store[job.id] = job
        return job
