"""Tests for ensemble fusion."""

import pytest

from support.ml_fixtures import sample_diff, sample_graph

from code_impact.domain.entities import SimilarCommit
from code_impact.domain.value_objects.risk import (
    AffectedFilePrediction,
    ConfidenceScore,
    RegressionProbability,
    RiskScore,
)
from code_impact.ml.inference.mock_gnn_predictor import MockGNNPredictor
from code_impact.ml.risk.classical_risk_classifier import ClassicalRiskClassifier
from code_impact.ml.risk.ensemble_fusion import EnsembleFusionService
from code_impact.domain.services import GNNPredictionResult


@pytest.mark.asyncio
async def test_ensemble_fusion_combines_signals():
    gnn = await MockGNNPredictor().predict(sample_graph(), sample_diff())
    classical = ClassicalRiskClassifier().predict(sample_diff(), [])
    fused = EnsembleFusionService().fuse(
        gnn,
        classical,
        [SimilarCommit("abc", 0.8, "msg", False)],
    )
    assert 0 <= fused.risk_score.value <= 100
    assert 0 <= fused.regression_probability.value <= 1
    assert 0 <= fused.confidence_score.value <= 1
    assert fused.fusion_weights["gnn"] > 0


def test_ensemble_merge_affected_files():
    gnn_result = GNNPredictionResult(
        risk_score=RiskScore(50),
        regression_probability=RegressionProbability(0.5),
        confidence_score=ConfidenceScore(0.6),
        affected_files=[
            AffectedFilePrediction("a.py", 0.8, 0.7, 1),
            AffectedFilePrediction("b.py", 0.4, 0.3, 2),
        ],
        node_importance={},
        edge_importance=[],
    )
    classical = ClassicalRiskClassifier().predict(sample_diff(), [])
    fused = EnsembleFusionService().fuse(gnn_result, classical, [])
    paths = [f.file_path for f in fused.affected_files]
    assert "a.py" in paths
