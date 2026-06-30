"""Orchestrates dependency graph construction and persistence."""

from __future__ import annotations

from uuid import UUID

from code_impact.domain.entities import GraphSnapshot
from code_impact.domain.exceptions import EntityNotFoundError
from code_impact.domain.repositories import IGraphRepository, IRepositoryRepository
from code_impact.domain.services import IGraphBuilder
from code_impact.infrastructure.config.logging import get_logger
from code_impact.infrastructure.graph.graph_storage import GraphStorage

logger = get_logger(__name__)


class GraphBuildService:
    def __init__(
        self,
        graph_builder: IGraphBuilder,
        graph_repo: IGraphRepository,
        repository_repo: IRepositoryRepository,
        graph_storage: GraphStorage,
    ) -> None:
        self._builder = graph_builder
        self._graph_repo = graph_repo
        self._repository_repo = repository_repo
        self._storage = graph_storage

    async def build_and_persist(self, repository_id: UUID, commit_sha: str) -> GraphSnapshot:
        repository = await self._repository_repo.get_by_id(repository_id)
        if not repository:
            raise EntityNotFoundError("Repository", repository_id)

        existing = await self._graph_repo.get_snapshot_by_sha(repository_id, commit_sha)
        if existing:
            logger.info("graph_snapshot_exists", repository_id=str(repository_id), sha=commit_sha)
            return existing

        snapshot = await self._builder.build_from_repository(repository_id, commit_sha)
        storage_path = self._storage.save(snapshot)
        snapshot.storage_path = storage_path

        await self._graph_repo.save_snapshot(snapshot)
        logger.info(
            "graph_built",
            repository_id=str(repository_id),
            sha=commit_sha,
            nodes=snapshot.node_count,
            edges=snapshot.edge_count,
        )
        return snapshot
