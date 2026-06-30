"""In-memory vector store for unit tests."""

from __future__ import annotations

import math

from code_impact.domain.services.vector_store import IVectorStore, VectorPoint, VectorSearchResult


class InMemoryVectorStore(IVectorStore):
    def __init__(self) -> None:
        self._collections: dict[str, dict[str, VectorPoint]] = {}
        self._dimensions: dict[str, int] = {}

    async def ensure_collection(self, collection: str, dimension: int) -> None:
        self._collections.setdefault(collection, {})
        self._dimensions[collection] = dimension

    async def upsert(self, collection: str, points: list[VectorPoint]) -> None:
        store = self._collections.setdefault(collection, {})
        for point in points:
            store[point.id] = point

    async def search(
        self,
        collection: str,
        query_vector: list[float],
        *,
        limit: int = 10,
        filters: dict | None = None,
    ) -> list[VectorSearchResult]:
        store = self._collections.get(collection, {})
        results: list[VectorSearchResult] = []

        for point in store.values():
            if filters and not _matches_filters(point.payload, filters):
                continue
            score = _cosine_similarity(query_vector, point.vector)
            results.append(VectorSearchResult(id=point.id, score=score, payload=point.payload))

        results.sort(key=lambda r: r.score, reverse=True)
        return results[:limit]

    async def delete_by_filter(self, collection: str, filters: dict) -> None:
        store = self._collections.get(collection, {})
        to_delete = [pid for pid, p in store.items() if _matches_filters(p.payload, filters)]
        for pid in to_delete:
            del store[pid]


def _matches_filters(payload: dict, filters: dict) -> bool:
    return all(payload.get(k) == v for k, v in filters.items())


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    if len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b, strict=False))
    norm_a = math.sqrt(sum(x * x for x in a)) or 1.0
    norm_b = math.sqrt(sum(x * x for x in b)) or 1.0
    return dot / (norm_a * norm_b)
