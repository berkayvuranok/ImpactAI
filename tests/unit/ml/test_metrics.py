"""Tests for evaluation metrics."""

from code_impact.ml.evaluation.metrics import compute_metrics, precision_at_k


def test_compute_metrics_basic():
    preds = [{"risk_score": 50.0, "regression_probability": 0.8}]
    labels = [{"risk_score": 45.0, "is_regression": 1.0, "affected_files": []}]
    metrics = compute_metrics(preds, labels)
    assert metrics["count"] == 1.0
    assert metrics["risk_mae"] == 5.0


def test_precision_at_k():
    ranked = [("a.py", 0.9), ("b.py", 0.7), ("c.py", 0.2)]
    score = precision_at_k(ranked, {"a.py", "c.py"}, k=2)
    assert score == 0.5
