"""Historical similarity search via vector store."""

from __future__ import annotations

from uuid import UUID

from code_impact.domain.entities import SimilarCommit
from code_impact.domain.services import IEmbeddingService, IHistoricalSearch
from code_impact.domain.services.vector_store import IVectorStore
from code_impact.infrastructure.config.settings import Settings


class HistoricalSearchService(IHistoricalSearch):
    def __init__(
        self,
        vector_store: IVectorStore,
        embedding_service: IEmbeddingService,
        settings: Settings,
    ) -> None:
        self._store = vector_store
        self._embeddings = embedding_service
        self._settings = settings

    async def find_similar_commits(
        self,
        repository_id: UUID,
        diff_embedding: list[float],
        top_k: int = 10,
    ) -> list[SimilarCommit]:
        await self._store.ensure_collection(
            self._settings.qdrant_collection_commits,
            self._embeddings.dimension,
        )
        results = await self._store.search(
            self._settings.qdrant_collection_commits,
            diff_embedding,
            limit=top_k,
            filters={"repository_id": str(repository_id)},
        )
        return [
            SimilarCommit(
                commit_sha=r.payload.get("commit_sha", ""),
                similarity_score=r.score,
                message=r.payload.get("message", ""),
                is_regression=bool(r.payload.get("is_regression", False)),
                linked_issue_ids=r.payload.get("linked_issue_ids", []),
            )
            for r in results
            if r.payload.get("commit_sha")
        ]

    async def find_similar_bugs(
        self,
        repository_id: UUID,
        diff_embedding: list[float],
        top_k: int = 5,
    ) -> list[dict]:
        await self._store.ensure_collection(
            self._settings.qdrant_collection_issues,
            self._embeddings.dimension,
        )
        results = await self._store.search(
            self._settings.qdrant_collection_issues,
            diff_embedding,
            limit=top_k,
            filters={"repository_id": str(repository_id)},
        )
        return [
            {
                "issue_id": r.payload.get("external_id", r.id),
                "title": r.payload.get("title", ""),
                "issue_type": r.payload.get("issue_type", "bug"),
                "similarity_score": r.score,
                "state": r.payload.get("state", "open"),
            }
            for r in results
        ]

    async def search_by_diff_text(
        self,
        repository_id: UUID,
        diff_text: str,
        *,
        top_k_commits: int = 10,
        top_k_bugs: int = 5,
    ) -> tuple[list[SimilarCommit], list[dict]]:
        embedding = await self._embeddings.embed_text(diff_text)
        commits = await self.find_similar_commits(repository_id, embedding, top_k_commits)
        bugs = await self.find_similar_bugs(repository_id, embedding, top_k_bugs)
        return commits, bugs
