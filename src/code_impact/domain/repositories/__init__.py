"""Repository interfaces — ports in hexagonal architecture."""

from abc import ABC, abstractmethod
from uuid import UUID

from code_impact.domain.entities import (
    Commit,
    EmbeddingRecord,
    GraphSnapshot,
    Issue,
    MLModel,
    Prediction,
    PullRequest,
    Repository,
    ReviewerProfile,
    SyncJob,
    User,
)
from code_impact.domain.value_objects.enums import PredictionStatus


class IUserRepository(ABC):
    @abstractmethod
    async def get_by_id(self, user_id: UUID) -> User | None: ...

    @abstractmethod
    async def get_by_email(self, email: str) -> User | None: ...

    @abstractmethod
    async def create(self, user: User) -> User: ...


class IRepositoryRepository(ABC):
    @abstractmethod
    async def get_by_id(self, repository_id: UUID) -> Repository | None: ...

    @abstractmethod
    async def get_by_url(self, url: str) -> Repository | None: ...

    @abstractmethod
    async def list_by_owner(self, owner_id: UUID) -> list[Repository]: ...

    @abstractmethod
    async def create(self, repository: Repository) -> Repository: ...

    @abstractmethod
    async def update(self, repository: Repository) -> Repository: ...

    @abstractmethod
    async def delete(self, repository_id: UUID) -> None: ...

    @abstractmethod
    async def find_by_normalized_url(self, url: str) -> Repository | None: ...


class ICommitRepository(ABC):
    @abstractmethod
    async def get_by_sha(self, repository_id: UUID, sha: str) -> Commit | None: ...

    @abstractmethod
    async def list_by_repository(
        self, repository_id: UUID, limit: int = 100, offset: int = 0
    ) -> list[Commit]: ...

    @abstractmethod
    async def create_batch(self, commits: list[Commit]) -> list[Commit]: ...


class IPullRequestRepository(ABC):
    @abstractmethod
    async def get_by_id(self, pr_id: UUID) -> PullRequest | None: ...

    @abstractmethod
    async def get_by_number(self, repository_id: UUID, pr_number: int) -> PullRequest | None: ...

    @abstractmethod
    async def create(self, pull_request: PullRequest) -> PullRequest: ...


class IPredictionRepository(ABC):
    @abstractmethod
    async def get_by_id(self, prediction_id: UUID) -> Prediction | None: ...

    @abstractmethod
    async def list_by_repository(
        self,
        repository_id: UUID,
        status: PredictionStatus | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Prediction]: ...

    @abstractmethod
    async def create(self, prediction: Prediction) -> Prediction: ...

    @abstractmethod
    async def update(self, prediction: Prediction) -> Prediction: ...

    @abstractmethod
    async def count_by_repository(self, repository_id: UUID) -> int: ...


class IGraphRepository(ABC):
    @abstractmethod
    async def get_latest_snapshot(self, repository_id: UUID) -> GraphSnapshot | None: ...

    @abstractmethod
    async def get_snapshot_by_sha(
        self, repository_id: UUID, commit_sha: str
    ) -> GraphSnapshot | None: ...

    @abstractmethod
    async def save_snapshot(self, snapshot: GraphSnapshot) -> GraphSnapshot: ...


class ISyncJobRepository(ABC):
    @abstractmethod
    async def get_by_id(self, job_id: UUID) -> SyncJob | None: ...

    @abstractmethod
    async def create(self, job: SyncJob) -> SyncJob: ...

    @abstractmethod
    async def update(self, job: SyncJob) -> SyncJob: ...


class IIssueRepository(ABC):
    @abstractmethod
    async def list_by_repository(
        self, repository_id: UUID, limit: int = 500, offset: int = 0
    ) -> list[Issue]: ...

    @abstractmethod
    async def create_batch(self, issues: list[Issue]) -> list[Issue]: ...


class IReviewerProfileRepository(ABC):
    @abstractmethod
    async def list_by_repository(self, repository_id: UUID) -> list[ReviewerProfile]: ...

    @abstractmethod
    async def create_batch(self, profiles: list[ReviewerProfile]) -> list[ReviewerProfile]: ...


class IModelRepository(ABC):
    @abstractmethod
    async def get_active(self, name: str) -> MLModel | None: ...

    @abstractmethod
    async def create(self, model: MLModel) -> MLModel: ...

    @abstractmethod
    async def set_active(self, model_id: UUID) -> None: ...


class IEmbeddingRepository(ABC):
    @abstractmethod
    async def get_by_entity(
        self, repository_id: UUID, entity_type: str, entity_id: UUID
    ) -> EmbeddingRecord | None: ...

    @abstractmethod
    async def list_by_repository(
        self, repository_id: UUID, entity_type: str | None = None
    ) -> list[EmbeddingRecord]: ...

    @abstractmethod
    async def create(self, record: EmbeddingRecord) -> EmbeddingRecord: ...

    @abstractmethod
    async def create_batch(self, records: list[EmbeddingRecord]) -> list[EmbeddingRecord]: ...
