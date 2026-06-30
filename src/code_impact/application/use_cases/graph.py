"""Graph-related use cases."""

from dataclasses import dataclass
from uuid import UUID

from code_impact.application.services.graph_build_service import GraphBuildService
from code_impact.domain.entities import GraphSnapshot
from code_impact.domain.exceptions import EntityNotFoundError
from code_impact.domain.repositories import IGraphRepository
from code_impact.infrastructure.graph.subgraph_extractor import extract_subgraph, seeds_for_files


@dataclass
class BuildGraphCommand:
    repository_id: UUID
    commit_sha: str


@dataclass
class GetSubgraphQuery:
    repository_id: UUID
    file_paths: list[str]
    commit_sha: str | None = None
    max_depth: int = 2


class BuildGraphUseCase:
    def __init__(self, graph_build_service: GraphBuildService) -> None:
        self._service = graph_build_service

    async def execute(self, command: BuildGraphCommand) -> GraphSnapshot:
        return await self._service.build_and_persist(command.repository_id, command.commit_sha)


class GetGraphUseCase:
    def __init__(self, graph_repo: IGraphRepository) -> None:
        self._graph_repo = graph_repo

    async def execute_latest(self, repository_id: UUID) -> GraphSnapshot:
        snapshot = await self._graph_repo.get_latest_snapshot(repository_id)
        if not snapshot:
            raise EntityNotFoundError("GraphSnapshot", repository_id)
        return snapshot

    async def execute_by_sha(self, repository_id: UUID, commit_sha: str) -> GraphSnapshot:
        snapshot = await self._graph_repo.get_snapshot_by_sha(repository_id, commit_sha)
        if not snapshot:
            raise EntityNotFoundError("GraphSnapshot", f"{repository_id}@{commit_sha}")
        return snapshot


class GetSubgraphUseCase:
    def __init__(self, graph_repo: IGraphRepository) -> None:
        self._graph_repo = graph_repo

    async def execute(self, query: GetSubgraphQuery) -> GraphSnapshot:
        if query.commit_sha:
            snapshot = await self._graph_repo.get_snapshot_by_sha(query.repository_id, query.commit_sha)
        else:
            snapshot = await self._graph_repo.get_latest_snapshot(query.repository_id)
        if not snapshot:
            raise EntityNotFoundError("GraphSnapshot", query.repository_id)

        seeds = seeds_for_files(snapshot, query.file_paths)
        sub_nodes, sub_edges = extract_subgraph(snapshot, seeds, max_depth=query.max_depth)

        return GraphSnapshot(
            id=snapshot.id,
            repository_id=snapshot.repository_id,
            commit_sha=snapshot.commit_sha,
            node_count=len(sub_nodes),
            edge_count=len(sub_edges),
            storage_path=snapshot.storage_path,
            created_at=snapshot.created_at,
            nodes=sub_nodes,
            edges=sub_edges,
        )
