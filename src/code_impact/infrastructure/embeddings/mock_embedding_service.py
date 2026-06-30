"""Deterministic embedding service for tests — no ML dependencies."""

from __future__ import annotations

import hashlib
import math

from code_impact.domain.services import IEmbeddingService


class MockEmbeddingService(IEmbeddingService):
    def __init__(self, dimension: int = 384) -> None:
        self._dimension = dimension
        self._model_name = "mock-embedding-v1"

    @property
    def model_name(self) -> str:
        return self._model_name

    @property
    def dimension(self) -> int:
        return self._dimension

    async def embed_text(self, text: str) -> list[float]:
        return self._vectorize(text)

    async def embed_code(self, code: str, language: str) -> list[float]:
        return self._vectorize(f"[{language}]{code}")

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        return [self._vectorize(t) for t in texts]

    def _vectorize(self, text: str) -> list[float]:
        digest = hashlib.sha256(text.encode()).digest()
        values: list[float] = []
        while len(values) < self._dimension:
            for byte in digest:
                values.append((byte / 255.0) * 2 - 1)
                if len(values) >= self._dimension:
                    break
            digest = hashlib.sha256(digest).digest()
        norm = math.sqrt(sum(v * v for v in values)) or 1.0
        return [v / norm for v in values]
