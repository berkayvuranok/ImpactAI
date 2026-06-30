"""Embedding indexing endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse

from code_impact.application.schemas import IndexEmbeddingsResponse
from code_impact.application.use_cases.embedding import IndexEmbeddingsCommand, IndexEmbeddingsUseCase
from code_impact.domain.exceptions import EntityNotFoundError
from code_impact.infrastructure.queue.task_dispatcher import ITaskDispatcher
from code_impact.presentation.api.dependencies import (
    get_index_embeddings_use_case,
    get_task_dispatcher,
)

router = APIRouter(prefix="/embeddings")


@router.post("/index/{repository_id}")
async def index_embeddings(
    repository_id: UUID,
    reindex: bool = Query(default=False),
    include_issues: bool = Query(default=True),
    async_index: bool = Query(default=False),
    use_case: IndexEmbeddingsUseCase = Depends(get_index_embeddings_use_case),
    dispatcher: ITaskDispatcher = Depends(get_task_dispatcher),
):
    """Index commit and issue embeddings into Qdrant."""
    if async_index:
        dispatcher.dispatch_index_embeddings(str(repository_id), reindex, include_issues)
        return JSONResponse(
            status_code=202,
            content={
                "message": "Embedding index job queued",
                "repository_id": str(repository_id),
            },
        )

    try:
        result = await use_case.execute(
            IndexEmbeddingsCommand(
                repository_id=repository_id,
                reindex=reindex,
                include_issues=include_issues,
            )
        )
    except EntityNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return IndexEmbeddingsResponse(
        repository_id=repository_id,
        commits_indexed=result["commits"]["indexed"],
        commits_skipped=result["commits"]["skipped"],
        issues_indexed=result["issues"]["indexed"],
        issues_skipped=result["issues"]["skipped"],
    )
