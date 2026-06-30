"""Semantic search endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends

from code_impact.application.schemas import SearchSimilarRequest, SearchSimilarResponse, SimilarCommitResponse
from code_impact.application.use_cases.embedding import SearchSimilarCommand, SearchSimilarUseCase
from code_impact.presentation.api.dependencies import get_search_similar_use_case

router = APIRouter(prefix="/search")


@router.post("/similar", response_model=SearchSimilarResponse)
async def search_similar(
    body: SearchSimilarRequest,
    use_case: SearchSimilarUseCase = Depends(get_search_similar_use_case),
) -> SearchSimilarResponse:
    """
    Find similar historical commits and bugs for a diff.

    Uses vector similarity in Qdrant — not LLM prediction.
    """
    result = await use_case.execute(
        SearchSimilarCommand(
            repository_id=body.repository_id,
            diff=body.diff,
            top_k_commits=body.top_k_commits,
            top_k_bugs=body.top_k_bugs,
        )
    )
    return SearchSimilarResponse(
        repository_id=body.repository_id,
        similar_commits=[
            SimilarCommitResponse(**c) for c in result["similar_commits"]
        ],
        similar_bugs=result["similar_bugs"],
    )


@router.get("/similar/{repository_id}", response_model=SearchSimilarResponse)
async def search_similar_get(
    repository_id: UUID,
    diff: str,
    top_k_commits: int = 10,
    top_k_bugs: int = 5,
    use_case: SearchSimilarUseCase = Depends(get_search_similar_use_case),
) -> SearchSimilarResponse:
    """GET variant for quick diff similarity lookups."""
    result = await use_case.execute(
        SearchSimilarCommand(
            repository_id=repository_id,
            diff=diff,
            top_k_commits=top_k_commits,
            top_k_bugs=top_k_bugs,
        )
    )
    return SearchSimilarResponse(
        repository_id=repository_id,
        similar_commits=[
            SimilarCommitResponse(**c) for c in result["similar_commits"]
        ],
        similar_bugs=result["similar_bugs"],
    )
