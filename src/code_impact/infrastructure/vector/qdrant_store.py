"""Qdrant vector database adapter."""

from __future__ import annotations

from qdrant_client import AsyncQdrantClient
from qdrant_client.models import (
    Distance,
    FieldCondition,
    Filter,
    MatchValue,
    PointStruct,
    VectorParams,
)

from code_impact.domain.services.vector_store import IVectorStore, VectorPoint, VectorSearchResult
from code_impact.infrastructure.config.logging import get_logger

logger = get_logger(__name__)


class QdrantVectorStore(IVectorStore):
    def __init__(self, host: str, port: int) -> None:
        self._client = AsyncQdrantClient(host=host, port=port)
        self._initialized: set[str] = set()

    async def ensure_collection(self, collection: str, dimension: int) -> None:
        if collection in self._initialized:
            return
        exists = await self._client.collection_exists(collection)
        if not exists:
            await self._client.create_collection(
                collection_name=collection,
                vectors_config=VectorParams(size=dimension, distance=Distance.COSINE),
            )
            logger.info("qdrant_collection_created", collection=collection, dimension=dimension)
        self._initialized.add(collection)

    async def upsert(self, collection: str, points: list[VectorPoint]) -> None:
        if not points:
            return
        await self._client.upsert(
            collection_name=collection,
            points=[
                PointStruct(id=p.id, vector=p.vector, payload=p.payload) for p in points
            ],
        )

    async def search(
        self,
        collection: str,
        query_vector: list[float],
        *,
        limit: int = 10,
        filters: dict | None = None,
    ) -> list[VectorSearchResult]:
        qdrant_filter = _build_filter(filters) if filters else None
        response = await self._client.search(
            collection_name=collection,
            query_vector=query_vector,
            limit=limit,
            query_filter=qdrant_filter,
        )
        return [
            VectorSearchResult(
                id=str(hit.id),
                score=hit.score,
                payload=hit.payload or {},
            )
            for hit in response
        ]

    async def delete_by_filter(self, collection: str, filters: dict) -> None:
        qdrant_filter = _build_filter(filters)
        if qdrant_filter is None:
            return
        await self._client.delete(collection_name=collection, points_selector=qdrant_filter)


def _build_filter(filters: dict | None) -> Filter | None:
    if not filters:
        return None
    conditions = [
        FieldCondition(key=key, match=MatchValue(value=value))
        for key, value in filters.items()
    ]
    return Filter(must=conditions)
