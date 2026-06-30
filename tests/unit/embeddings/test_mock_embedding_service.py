"""Unit tests for MockEmbeddingService."""

import pytest

from code_impact.infrastructure.embeddings.mock_embedding_service import MockEmbeddingService


@pytest.fixture
def service() -> MockEmbeddingService:
    return MockEmbeddingService(dimension=384)


@pytest.mark.asyncio
async def test_embed_text_deterministic(service: MockEmbeddingService):
    v1 = await service.embed_text("hello world")
    v2 = await service.embed_text("hello world")
    v3 = await service.embed_text("different")
    assert v1 == v2
    assert v1 != v3
    assert len(v1) == 384


@pytest.mark.asyncio
async def test_embed_batch(service: MockEmbeddingService):
    vectors = await service.embed_batch(["a", "b"])
    assert len(vectors) == 2
    assert len(vectors[0]) == 384


@pytest.mark.asyncio
async def test_embed_code(service: MockEmbeddingService):
    vector = await service.embed_code("def foo(): pass", "python")
    assert len(vector) == 384
