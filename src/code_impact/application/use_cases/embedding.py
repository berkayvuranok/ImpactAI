"""Embedding and search use cases."""

from dataclasses import dataclass
from uuid import UUID

from code_impact.application.services.embedding_index_service import EmbeddingIndexService
from code_impact.domain.entities import SimilarCommit
from code_impact.infrastructure.search.historical_search_service import HistoricalSearchService


@dataclass
class IndexEmbeddingsCommand:
    repository_id: UUID
    reindex: bool = False
    include_issues: bool = True


@dataclass
class SearchSimilarCommand:
    repository_id: UUID
    diff: str
    top_k_commits: int = 10
    top_k_bugs: int = 5


class IndexEmbeddingsUseCase:
    def __init__(self, index_service: EmbeddingIndexService) -> None:
        self._index = index_service

    async def execute(self, command: IndexEmbeddingsCommand) -> dict:
        commit_stats = await self._index.index_repository_commits(
            command.repository_id,
            reindex=command.reindex,
        )
        issue_stats = {"indexed": 0, "skipped": 0, "total": 0}
        if command.include_issues:
            issue_stats = await self._index.index_repository_issues(
                command.repository_id,
                reindex=command.reindex,
            )
        return {"commits": commit_stats, "issues": issue_stats}


class SearchSimilarUseCase:
    def __init__(self, search_service: HistoricalSearchService) -> None:
        self._search = search_service

    async def execute(self, command: SearchSimilarCommand) -> dict:
        commits, bugs = await self._search.search_by_diff_text(
            command.repository_id,
            command.diff,
            top_k_commits=command.top_k_commits,
            top_k_bugs=command.top_k_bugs,
        )
        return {
            "similar_commits": [_commit_to_dict(c) for c in commits],
            "similar_bugs": bugs,
        }


def _commit_to_dict(commit: SimilarCommit) -> dict:
    return {
        "commit_sha": commit.commit_sha,
        "similarity_score": commit.similarity_score,
        "message": commit.message,
        "is_regression": commit.is_regression,
        "linked_issue_ids": commit.linked_issue_ids,
    }
