"""Prediction pipeline Celery tasks."""

from __future__ import annotations

import asyncio
from uuid import UUID

from code_impact.application.services.prediction_pipeline_service import PredictionPipelineService
from code_impact.infrastructure.analysis.diff_analysis_service import DiffAnalysisService
from code_impact.infrastructure.config.logging import get_logger
from code_impact.infrastructure.config.settings import get_settings
from code_impact.infrastructure.embeddings.mock_embedding_service import MockEmbeddingService
from code_impact.infrastructure.embeddings.sentence_transformer_service import (
    SentenceTransformerEmbeddingService,
)
from code_impact.infrastructure.persistence.database import create_session_factory
from code_impact.infrastructure.persistence.repositories import (
    SqlAlchemyGraphRepository,
    SqlAlchemyPredictionRepository,
    SqlAlchemyReviewerProfileRepository,
)
from code_impact.infrastructure.queue.celery_app import celery_app
from code_impact.infrastructure.llm.factory import build_explanation_generator
from code_impact.infrastructure.recommendation.reviewer_recommender import ReviewerRecommender
from code_impact.infrastructure.search.historical_search_service import HistoricalSearchService
from code_impact.infrastructure.vector.qdrant_store import QdrantVectorStore
from code_impact.ml.inference.gnn_predictor import GNNPredictor
from code_impact.ml.inference.mock_gnn_predictor import MockGNNPredictor
from code_impact.ml.risk.ensemble_fusion import EnsembleFusionService

logger = get_logger(__name__)


def _build_pipeline(session) -> PredictionPipelineService:
    settings = get_settings()
    if settings.embedding_backend == "mock":
        embeddings = MockEmbeddingService()
    else:
        embeddings = SentenceTransformerEmbeddingService(settings.embedding_model)

    vector_store = QdrantVectorStore(host=settings.qdrant_host, port=settings.qdrant_port)
    search = HistoricalSearchService(vector_store, embeddings, settings)

    if settings.gnn_backend == "mock":
        gnn = MockGNNPredictor()
    else:
        predictor = GNNPredictor(settings.gnn_model_path, device=settings.inference_device)
        gnn = predictor if predictor.is_loaded else MockGNNPredictor()

    ensemble = EnsembleFusionService(
        gnn_weight=settings.ensemble_gnn_weight,
        classical_weight=settings.ensemble_classical_weight,
        historical_weight=settings.ensemble_historical_weight,
    )

    return PredictionPipelineService(
        prediction_repo=SqlAlchemyPredictionRepository(session),
        graph_repo=SqlAlchemyGraphRepository(session),
        diff_service=DiffAnalysisService(),
        gnn_predictor=gnn,
        historical_search=search,
        reviewer_recommender=ReviewerRecommender(SqlAlchemyReviewerProfileRepository(session)),
        embedding_service=embeddings,
        explanation_generator=build_explanation_generator(settings),
        ensemble=ensemble,
    )


async def _run_prediction_async(prediction_id: str) -> dict:
    settings = get_settings()
    session_factory = create_session_factory(settings)

    async with session_factory() as session:
        pipeline = _build_pipeline(session)
        prediction = await pipeline.run(UUID(prediction_id))
        await session.commit()
        return {
            "status": prediction.status.value,
            "prediction_id": str(prediction.id),
            "risk_score": prediction.risk_score.value if prediction.risk_score else None,
        }


@celery_app.task(name="prediction.run_pipeline", bind=True, max_retries=2)
def run_prediction_pipeline_task(self, prediction_id: str) -> dict:
    """Execute full GNN + ensemble + reviewer prediction pipeline."""
    try:
        return asyncio.run(_run_prediction_async(prediction_id))
    except Exception as exc:
        logger.exception("run_prediction_pipeline_failed", prediction_id=prediction_id)
        raise self.retry(exc=exc, countdown=20) from exc
