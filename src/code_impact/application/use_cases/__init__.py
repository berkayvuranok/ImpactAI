"""Application use cases — orchestration layer."""

from dataclasses import dataclass
from uuid import UUID

from code_impact.domain.entities import Prediction, Repository, SyncJob
from code_impact.domain.exceptions import EntityNotFoundError
from code_impact.domain.repositories import (
    IPredictionRepository,
    IRepositoryRepository,
    ISyncJobRepository,
)
from code_impact.domain.services.analysis_types import EnrichedDiffAnalysisResult
from code_impact.domain.value_objects.enums import RepositoryProvider
from code_impact.infrastructure.analysis.diff_analysis_service import DiffAnalysisService


@dataclass
class CreateRepositoryCommand:
    owner_id: UUID
    name: str
    url: str
    default_branch: str = "main"
    provider: RepositoryProvider = RepositoryProvider.GITHUB


@dataclass
class SyncRepositoryCommand:
    repository_id: UUID
    full_sync: bool = False
    since_sha: str | None = None


@dataclass
class AnalyzeDiffCommand:
    diff: str
    file_contents_before: dict[str, str] | None = None
    file_contents_after: dict[str, str] | None = None


@dataclass
class PredictImpactCommand:
    repository_id: UUID
    created_by: UUID
    diff: str
    base_sha: str | None = None
    head_sha: str | None = None
    pull_request_id: UUID | None = None


class CreateRepositoryUseCase:
    def __init__(self, repository_repo: IRepositoryRepository) -> None:
        self._repository_repo = repository_repo

    async def execute(self, command: CreateRepositoryCommand) -> Repository:
        from uuid import uuid4

        existing = await self._repository_repo.get_by_url(command.url)
        if existing:
            return existing

        repository = Repository(
            id=uuid4(),
            owner_id=command.owner_id,
            name=command.name,
            url=command.url,
            default_branch=command.default_branch,
            provider=command.provider,
        )
        return await self._repository_repo.create(repository)


class GetRepositoryUseCase:
    def __init__(self, repository_repo: IRepositoryRepository) -> None:
        self._repository_repo = repository_repo

    async def execute(self, repository_id: UUID) -> Repository:
        repository = await self._repository_repo.get_by_id(repository_id)
        if not repository:
            raise EntityNotFoundError("Repository", repository_id)
        return repository


class SyncRepositoryUseCase:
    def __init__(
        self,
        repository_repo: IRepositoryRepository,
        sync_job_repo: ISyncJobRepository,
    ) -> None:
        self._repository_repo = repository_repo
        self._sync_job_repo = sync_job_repo

    async def execute(self, command: SyncRepositoryCommand) -> SyncJob:
        repository = await self._repository_repo.get_by_id(command.repository_id)
        if not repository:
            raise EntityNotFoundError("Repository", command.repository_id)

        job = SyncJob.create(repository_id=command.repository_id)
        job = await self._sync_job_repo.create(job)
        return job


class AnalyzeDiffUseCase:
    def __init__(self, analysis_service: DiffAnalysisService | None = None) -> None:
        self._analysis_service = analysis_service or DiffAnalysisService()

    async def execute(self, command: AnalyzeDiffCommand) -> EnrichedDiffAnalysisResult:
        return await self._analysis_service.analyze(
            diff=command.diff,
            file_contents_before=command.file_contents_before,
            file_contents_after=command.file_contents_after,
        )


class PredictImpactUseCase:
    """CQRS Command: initiates async prediction pipeline."""

    def __init__(
        self,
        prediction_repo: IPredictionRepository,
        repository_repo: IRepositoryRepository,
    ) -> None:
        self._prediction_repo = prediction_repo
        self._repository_repo = repository_repo

    async def execute(self, command: PredictImpactCommand) -> Prediction:
        repository = await self._repository_repo.get_by_id(command.repository_id)
        if not repository:
            raise EntityNotFoundError("Repository", command.repository_id)

        prediction = Prediction.create_pending(
            repository_id=command.repository_id,
            created_by=command.created_by,
            input_payload={
                "diff": command.diff,
                "base_sha": command.base_sha,
                "head_sha": command.head_sha,
            },
            pull_request_id=command.pull_request_id,
        )
        return await self._prediction_repo.create(prediction)


class GetPredictionUseCase:
    def __init__(self, prediction_repo: IPredictionRepository) -> None:
        self._prediction_repo = prediction_repo

    async def execute(self, prediction_id: UUID) -> Prediction:
        prediction = await self._prediction_repo.get_by_id(prediction_id)
        if not prediction:
            raise EntityNotFoundError("Prediction", prediction_id)
        return prediction
