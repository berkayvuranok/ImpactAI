"""Tests for domain value objects."""

import pytest

from code_impact.domain.value_objects.risk import (
    AffectedFilePrediction,
    ConfidenceScore,
    RegressionProbability,
    RiskScore,
)


class TestRiskScore:
    def test_valid_score(self):
        score = RiskScore(42.5)
        assert score.value == 42.5
        assert score.level == "medium"

    def test_low_risk(self):
        assert RiskScore(10.0).level == "low"

    def test_critical_risk(self):
        assert RiskScore(90.0).level == "critical"

    def test_invalid_score_raises(self):
        with pytest.raises(ValueError, match="Risk score must be"):
            RiskScore(150.0)


class TestRegressionProbability:
    def test_valid_probability(self):
        prob = RegressionProbability(0.75)
        assert prob.value == 0.75

    def test_invalid_probability_raises(self):
        with pytest.raises(ValueError):
            RegressionProbability(1.5)


class TestAffectedFilePrediction:
    def test_valid_prediction(self):
        pred = AffectedFilePrediction(
            file_path="src/main.py",
            break_probability=0.8,
            node_importance=0.6,
            rank=1,
        )
        assert pred.file_path == "src/main.py"

    def test_invalid_rank_raises(self):
        with pytest.raises(ValueError, match="Rank must be"):
            AffectedFilePrediction(
                file_path="src/main.py",
                break_probability=0.8,
                node_importance=0.6,
                rank=0,
            )
