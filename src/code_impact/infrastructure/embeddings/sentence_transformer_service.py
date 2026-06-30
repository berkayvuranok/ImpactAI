"""Sentence Transformers embedding service — runs inference in thread pool."""

from __future__ import annotations

import asyncio
from functools import lru_cache

from code_impact.domain.services import IEmbeddingService
from code_impact.infrastructure.config.logging import get_logger

logger = get_logger(__name__)


@lru_cache(maxsize=1)
def _load_model(model_name: str):
    from sentence_transformers import SentenceTransformer

    logger.info("loading_embedding_model", model=model_name)
    return SentenceTransformer(model_name)


class SentenceTransformerEmbeddingService(IEmbeddingService):
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2") -> None:
        self._model_name = model_name
        self._dimension: int | None = None

    @property
    def model_name(self) -> str:
        return self._model_name

    @property
    def dimension(self) -> int:
        if self._dimension is None:
            model = _load_model(self._model_name)
            self._dimension = model.get_sentence_embedding_dimension()
        return self._dimension

    async def embed_text(self, text: str) -> list[float]:
        vectors = await self.embed_batch([text])
        return vectors[0]

    async def embed_code(self, code: str, language: str) -> list[float]:
        prefixed = f"Language: {language}\n{code}"
        return await self.embed_text(prefixed)

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        return await asyncio.to_thread(self._encode_sync, texts)

    def _encode_sync(self, texts: list[str]) -> list[list[float]]:
        model = _load_model(self._model_name)
        embeddings = model.encode(texts, normalize_embeddings=True, show_progress_bar=False)
        return [vec.tolist() for vec in embeddings]
