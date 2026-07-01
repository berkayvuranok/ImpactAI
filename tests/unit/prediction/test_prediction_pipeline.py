"""Tests for prediction pipeline service."""

from uuid import uuid4

import pytest

from code_impact.application.services.prediction_pipeline_service import PredictionPipelineService
from code_impact.application.use_cases import PredictImpactCommand, PredictImpactUseCase
from code_impact.domain.value_objects.enums import PredictionStatus, RepositoryProvider
from code_impact.domain.entities import Repository
from code_impact.infrastructure.analysis.diff_analysis_service import DiffAnalysisService
from code_impact.infrastructure.embeddings.mock_embedding_service import MockEmbeddingService
from code_impact.infrastructure.recommendation.reviewer_recommender import ReviewerRecommender
from code_impact.infrastructure.llm.template_explanation_generator import TemplateExplanationGenerator
from code_impact.infrastructure.search.historical_search_service import HistoricalSearchService
from code_impact.infrastructure.config.settings import Settings
from code_impact.ml.inference.mock_gnn_predictor import MockGNNPredictor
from code_impact.presentation.api.dependencies import SYSTEM_USER_ID
from support.in_memory_repositories import InMemoryRepositoryRepository
from support.in_memory_graph_repository import InMemoryGraphRepository
from support.in_memory_prediction_repositories import (
    InMemoryPredictionRepository,
    InMemoryReviewerProfileRepository,
)
from code_impact.infrastructure.vector.in_memory_vector_store import InMemoryVectorStore

SAMPLE_DIFF = """\
diff --git a/a.py b/a.py
--- a/a.py
+++ b/a.py
@@ -1 +1,2 @@
 x = 1
+y = 2
"""


def _settings() -> Settings:
    return Settings(
        secret_key="test-secret-key-minimum-32-chars-long",
        database_url="postgresql+asyncpg://cip:cip_secret@localhost:5432/code_impact_test",
        redis_url="redis://localhost:6379/0",
        celery_broker_url="redis://localhost:6379/1",
        celery_result_backend="redis://localhost:6379/2",
        embedding_backend="mock",
    )


@pytest.mark.asyncio
async def test_prediction_pipeline_completes():
    repo_id = uuid4()
    pred_repo = InMemoryPredictionRepository()
    graph_repo = InMemoryGraphRepository()
    reviewer_repo = InMemoryReviewerProfileRepository()
    repo_repo = InMemoryRepositoryRepository()

    repository = Repository(
        id=repo_id,
        owner_id=SYSTEM_USER_ID,
        name="test",
        url="https://github.com/example/test",
        default_branch="main",
        provider=RepositoryProvider.GITHUB,
    )
    await repo_repo.create(repository)

    settings = _settings()
    embeddings = MockEmbeddingService()
    search = HistoricalSearchService(InMemoryVectorStore(), embeddings, settings)

    pipeline = PredictionPipelineService(
        prediction_repo=pred_repo,
        graph_repo=graph_repo,
        diff_service=DiffAnalysisService(),
        gnn_predictor=MockGNNPredictor(),
        historical_search=search,
        reviewer_recommender=ReviewerRecommender(reviewer_repo),
        embedding_service=embeddings,
        explanation_generator=TemplateExplanationGenerator(),
    )

    predict_uc = PredictImpactUseCase(pred_repo, repo_repo)
    prediction = await predict_uc.execute(
        PredictImpactCommand(
            repository_id=repo_id,
            created_by=SYSTEM_USER_ID,
            diff=SAMPLE_DIFF,
        )
    )
    result = await pipeline.run(prediction.id)

    assert result.status == PredictionStatus.COMPLETED
    assert result.risk_score is not None
    assert result.regression_probability is not None
    assert result.confidence_score is not None
    assert result.explanation is not None
    assert result.explanation.root_cause
    assert "xai" in result.output_payload
    assert result.output_payload["xai"]["feature_attributions"]
