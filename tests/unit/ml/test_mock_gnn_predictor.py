"""Tests for mock GNN predictor."""

import pytest

from support.ml_fixtures import sample_diff, sample_graph

from code_impact.ml.inference.mock_gnn_predictor import MockGNNPredictor


@pytest.mark.asyncio
async def test_mock_gnn_predictor_returns_valid_scores():
    predictor = MockGNNPredictor()
    result = await predictor.predict(sample_graph(), sample_diff(), historical_embedding=[0.1] * 384)
    assert 0 <= result.risk_score.value <= 100
    assert 0 <= result.regression_probability.value <= 1
    assert result.affected_files
    assert result.affected_files[0].rank == 1
