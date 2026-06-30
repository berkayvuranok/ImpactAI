"""Unit tests for InMemoryVectorStore."""

import pytest

from code_impact.domain.services.vector_store import VectorPoint
from code_impact.infrastructure.vector.in_memory_vector_store import InMemoryVectorStore


@pytest.fixture
def store() -> InMemoryVectorStore:
    return InMemoryVectorStore()


@pytest.mark.asyncio
async def test_upsert_and_search(store: InMemoryVectorStore):
    await store.ensure_collection("commits", 3)
    await store.upsert(
        "commits",
        [
            VectorPoint(id="1", vector=[1.0, 0.0, 0.0], payload={"repository_id": "r1", "sha": "a"}),
            VectorPoint(id="2", vector=[0.9, 0.1, 0.0], payload={"repository_id": "r1", "sha": "b"}),
            VectorPoint(id="3", vector=[0.0, 1.0, 0.0], payload={"repository_id": "r2", "sha": "c"}),
        ],
    )

    results = await store.search(
        "commits",
        [1.0, 0.0, 0.0],
        limit=2,
        filters={"repository_id": "r1"},
    )
    assert len(results) == 2
    assert results[0].id == "1"
    assert results[0].score > results[1].score


@pytest.mark.asyncio
async def test_delete_by_filter(store: InMemoryVectorStore):
    await store.ensure_collection("issues", 2)
    await store.upsert(
        "issues",
        [VectorPoint(id="1", vector=[1.0, 0.0], payload={"repository_id": "r1"})],
    )
    await store.delete_by_filter("issues", {"repository_id": "r1"})
    results = await store.search("issues", [1.0, 0.0], limit=10)
    assert len(results) == 0
