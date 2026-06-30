"""Graph visualization and query endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse

from code_impact.application.schemas import GraphEdgeResponse, GraphNodeResponse, GraphResponse
from code_impact.application.use_cases.graph import (
    BuildGraphCommand,
    BuildGraphUseCase,
    GetGraphUseCase,
    GetSubgraphQuery,
    GetSubgraphUseCase,
)
from code_impact.domain.exceptions import EntityNotFoundError
from code_impact.infrastructure.queue.task_dispatcher import ITaskDispatcher
from code_impact.presentation.api.dependencies import (
    get_build_graph_use_case,
    get_get_graph_use_case,
    get_get_subgraph_use_case,
    get_task_dispatcher,
)

router = APIRouter(prefix="/graph")


def _to_response(snapshot) -> GraphResponse:
    return GraphResponse(
        snapshot_id=snapshot.id,
        commit_sha=snapshot.commit_sha,
        node_count=snapshot.node_count,
        edge_count=snapshot.edge_count,
        nodes=[
            GraphNodeResponse(
                node_id=n.node_id,
                node_type=n.node_type.value,
                name=n.name,
                file_path=n.file_path,
                properties=n.properties,
            )
            for n in snapshot.nodes
        ],
        edges=[
            GraphEdgeResponse(
                source_id=e.source_id,
                target_id=e.target_id,
                edge_type=e.edge_type.value,
                weight=e.weight,
            )
            for e in snapshot.edges
        ],
    )


@router.get("/{repository_id}", response_model=GraphResponse)
async def get_latest_graph(
    repository_id: UUID,
    use_case: GetGraphUseCase = Depends(get_get_graph_use_case),
) -> GraphResponse:
    """Return the latest dependency graph snapshot for a repository."""
    try:
        snapshot = await use_case.execute_latest(repository_id)
    except EntityNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return _to_response(snapshot)


@router.get("/{repository_id}/subgraph", response_model=GraphResponse)
async def get_subgraph(
    repository_id: UUID,
    files: list[str] = Query(..., description="Seed file paths"),
    commit_sha: str | None = None,
    max_depth: int = Query(default=2, ge=1, le=5),
    use_case: GetSubgraphUseCase = Depends(get_get_subgraph_use_case),
) -> GraphResponse:
    """BFS subgraph around changed/affected files."""
    try:
        snapshot = await use_case.execute(
            GetSubgraphQuery(
                repository_id=repository_id,
                file_paths=files,
                commit_sha=commit_sha,
                max_depth=max_depth,
            )
        )
    except EntityNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return _to_response(snapshot)


@router.post("/{repository_id}/build")
async def build_graph(
    repository_id: UUID,
    commit_sha: str = Query(..., min_length=7),
    async_build: bool = Query(default=False),
    use_case: BuildGraphUseCase = Depends(get_build_graph_use_case),
    dispatcher: ITaskDispatcher = Depends(get_task_dispatcher),
):
    """Build dependency graph at commit. Set async_build=true to queue via Celery."""
    if async_build:
        dispatcher.dispatch_build_graph(str(repository_id), commit_sha)
        return JSONResponse(
            status_code=202,
            content={
                "message": "Graph build queued",
                "repository_id": str(repository_id),
                "commit_sha": commit_sha,
            },
        )

    try:
        snapshot = await use_case.execute(
            BuildGraphCommand(repository_id=repository_id, commit_sha=commit_sha)
        )
    except EntityNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return _to_response(snapshot)


@router.get("/{repository_id}/{commit_sha}", response_model=GraphResponse)
async def get_graph_at_commit(
    repository_id: UUID,
    commit_sha: str,
    use_case: GetGraphUseCase = Depends(get_get_graph_use_case),
) -> GraphResponse:
    """Return dependency graph at a specific commit SHA."""
    try:
        snapshot = await use_case.execute_by_sha(repository_id, commit_sha)
    except EntityNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return _to_response(snapshot)
