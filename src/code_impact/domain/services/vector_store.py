"""Vector store port for embedding persistence and search."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True, slots=True)
class VectorPoint:
    id: str
    vector: list[float]
    payload: dict


@dataclass(frozen=True, slots=True)
class VectorSearchResult:
    id: str
    score: float
    payload: dict


class IVectorStore(ABC):
    @abstractmethod
    async def ensure_collection(self, collection: str, dimension: int) -> None: ...

    @abstractmethod
    async def upsert(self, collection: str, points: list[VectorPoint]) -> None: ...

    @abstractmethod
    async def search(
        self,
        collection: str,
        query_vector: list[float],
        *,
        limit: int = 10,
        filters: dict | None = None,
    ) -> list[VectorSearchResult]: ...

    @abstractmethod
    async def delete_by_filter(self, collection: str, filters: dict) -> None: ...
