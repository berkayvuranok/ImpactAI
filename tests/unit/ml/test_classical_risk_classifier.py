"""Tests for classical risk classifier."""

from support.ml_fixtures import sample_diff

from code_impact.domain.entities import SimilarCommit
from code_impact.ml.risk.classical_risk_classifier import ClassicalRiskClassifier


def test_classical_classifier_returns_bounded_scores():
    classifier = ClassicalRiskClassifier()
    similar = [
        SimilarCommit("abc", 0.9, "fix regression", True),
        SimilarCommit("def", 0.7, "normal change", False),
    ]
    result = classifier.predict(sample_diff(), similar)
    assert 0 <= result.risk_score.value <= 100
    assert 0 <= result.regression_probability.value <= 1


def test_classical_classifier_higher_with_regressions():
    classifier = ClassicalRiskClassifier()
    low = classifier.predict(sample_diff(), [])
    high = classifier.predict(
        sample_diff(),
        [SimilarCommit("x", 0.95, "bad", True), SimilarCommit("y", 0.9, "bad2", True)],
    )
    assert high.risk_score.value >= low.risk_score.value
