"""Repository management use cases."""

from uuid import UUID

from code_impact.domain.entities import Repository
from code_impact.domain.exceptions import AuthorizationError, EntityNotFoundError
from code_impact.domain.repositories import IRepositoryRepository


class ListRepositoriesUseCase:
    def __init__(self, repository_repo: IRepositoryRepository) -> None:
        self._repo = repository_repo

    async def execute(self, owner_id: UUID) -> list[Repository]:
        return await self._repo.list_by_owner(owner_id)


class DeleteRepositoryUseCase:
    def __init__(self, repository_repo: IRepositoryRepository) -> None:
        self._repo = repository_repo

    async def execute(self, repository_id: UUID, owner_id: UUID) -> None:
        repository = await self._repo.get_by_id(repository_id)
        if not repository:
            raise EntityNotFoundError("Repository", repository_id)
        if repository.owner_id != owner_id:
            raise AuthorizationError("Not allowed to delete this repository")
        await self._repo.delete(repository_id)
