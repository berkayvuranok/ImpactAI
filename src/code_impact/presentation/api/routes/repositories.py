"""Repository management endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from code_impact.application.schemas import (
    CreateRepositoryRequest,
    RepositoryResponse,
    SyncJobResponse,
    SyncRepositoryRequest,
)
from code_impact.application.use_cases import (
    CreateRepositoryCommand,
    CreateRepositoryUseCase,
    GetRepositoryUseCase,
    SyncRepositoryCommand,
    SyncRepositoryUseCase,
)
from code_impact.domain.exceptions import DomainError, EntityNotFoundError
from code_impact.domain.value_objects.enums import RepositoryProvider
from code_impact.infrastructure.queue.task_dispatcher import ITaskDispatcher
from code_impact.presentation.api.dependencies import (
    SYSTEM_USER_ID,
    get_create_repository_use_case,
    get_get_repository_use_case,
    get_sync_repository_use_case,
    get_task_dispatcher,
)

router = APIRouter(prefix="/repository")


def _to_response(repo) -> RepositoryResponse:
    return RepositoryResponse(
        id=repo.id,
        name=repo.name,
        url=repo.url,
        default_branch=repo.default_branch,
        provider=repo.provider.value,
        last_synced_at=repo.last_synced_at,
        created_at=repo.created_at,
    )


@router.post("", response_model=RepositoryResponse, status_code=status.HTTP_201_CREATED)
async def create_repository(
    body: CreateRepositoryRequest,
    use_case: CreateRepositoryUseCase = Depends(get_create_repository_use_case),
) -> RepositoryResponse:
    """Register a Git repository for impact analysis."""
    try:
        provider = RepositoryProvider(body.provider)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=f"Invalid provider: {body.provider}") from exc

    command = CreateRepositoryCommand(
        owner_id=SYSTEM_USER_ID,
        name=body.name,
        url=str(body.url),
        default_branch=body.default_branch,
        provider=provider,
    )
    repository = await use_case.execute(command)
    return _to_response(repository)


@router.get("/{repository_id}", response_model=RepositoryResponse)
async def get_repository(
    repository_id: UUID,
    use_case: GetRepositoryUseCase = Depends(get_get_repository_use_case),
) -> RepositoryResponse:
    try:
        repository = await use_case.execute(repository_id)
    except EntityNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return _to_response(repository)


@router.post("/{repository_id}/sync", response_model=SyncJobResponse)
async def sync_repository(
    repository_id: UUID,
    body: SyncRepositoryRequest,
    use_case: SyncRepositoryUseCase = Depends(get_sync_repository_use_case),
    dispatcher: ITaskDispatcher = Depends(get_task_dispatcher),
) -> SyncJobResponse:
    """Trigger repository sync: clone/pull, index commits."""
    command = SyncRepositoryCommand(
        repository_id=repository_id,
        full_sync=body.full_sync,
        since_sha=body.since_sha,
    )
    try:
        job = await use_case.execute(command)
    except EntityNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except DomainError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    dispatcher.dispatch_sync_repository(
        str(repository_id),
        str(job.id),
        body.full_sync,
        body.since_sha,
    )

    return SyncJobResponse(
        job_id=job.id,
        repository_id=repository_id,
        status=job.status.value,
        message="Repository sync job queued",
    )
