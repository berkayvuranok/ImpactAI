"""Repository management endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from code_impact.application.schemas import (
    CreateRepositoryRequest,
    RepositoryListResponse,
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
from code_impact.application.use_cases.repository import DeleteRepositoryUseCase, ListRepositoriesUseCase
from code_impact.domain.entities import User
from code_impact.domain.exceptions import AuthorizationError, DomainError, EntityNotFoundError
from code_impact.domain.value_objects.enums import RepositoryProvider
from code_impact.infrastructure.queue.task_dispatcher import ITaskDispatcher
from code_impact.presentation.api.dependencies import (
    get_create_repository_use_case,
    get_current_user,
    get_delete_repository_use_case,
    get_get_repository_use_case,
    get_list_repositories_use_case,
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


@router.get("", response_model=RepositoryListResponse)
async def list_repositories(
    current_user: User = Depends(get_current_user),
    use_case: ListRepositoriesUseCase = Depends(get_list_repositories_use_case),
) -> RepositoryListResponse:
    items = await use_case.execute(current_user.id)
    responses = [_to_response(r) for r in items]
    return RepositoryListResponse(items=responses, total=len(responses))


@router.post("", response_model=RepositoryResponse, status_code=status.HTTP_201_CREATED)
async def create_repository(
    body: CreateRepositoryRequest,
    current_user: User = Depends(get_current_user),
    use_case: CreateRepositoryUseCase = Depends(get_create_repository_use_case),
) -> RepositoryResponse:
    """Register a Git repository for impact analysis."""
    try:
        provider = RepositoryProvider(body.provider)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=f"Invalid provider: {body.provider}") from exc

    command = CreateRepositoryCommand(
        owner_id=current_user.id,
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
    current_user: User = Depends(get_current_user),
    use_case: GetRepositoryUseCase = Depends(get_get_repository_use_case),
) -> RepositoryResponse:
    try:
        repository = await use_case.execute(repository_id)
    except EntityNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    if repository.owner_id != current_user.id and current_user.role.value != "admin":
        raise HTTPException(status_code=403, detail="Not allowed to access this repository")
    return _to_response(repository)


@router.delete("/{repository_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_repository(
    repository_id: UUID,
    current_user: User = Depends(get_current_user),
    use_case: DeleteRepositoryUseCase = Depends(get_delete_repository_use_case),
) -> None:
    try:
        await use_case.execute(repository_id, current_user.id)
    except EntityNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except AuthorizationError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc


@router.post("/{repository_id}/sync", response_model=SyncJobResponse)
async def sync_repository(
    repository_id: UUID,
    body: SyncRepositoryRequest,
    current_user: User = Depends(get_current_user),
    get_repo: GetRepositoryUseCase = Depends(get_get_repository_use_case),
    use_case: SyncRepositoryUseCase = Depends(get_sync_repository_use_case),
    dispatcher: ITaskDispatcher = Depends(get_task_dispatcher),
) -> SyncJobResponse:
    """Trigger repository sync: clone/pull, index commits."""
    try:
        repository = await get_repo.execute(repository_id)
        if repository.owner_id != current_user.id and current_user.role.value != "admin":
            raise HTTPException(status_code=403, detail="Not allowed to sync this repository")
    except EntityNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    command = SyncRepositoryCommand(
        repository_id=repository_id,
        full_sync=body.full_sync,
        since_sha=body.since_sha,
    )
    try:
        job = await use_case.execute(command)
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
