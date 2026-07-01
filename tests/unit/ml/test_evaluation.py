"""Tests for evaluation framework."""

from pathlib import Path

import pytest

from code_impact.ml.evaluation import (
    BatchEvaluator,
    MetricTargets,
    aggregate_metrics,
    calibration_ece,
    load_benchmark,
    mean_reciprocal_rank,
    recall_at_k,
)


def test_recall_at_k_and_mrr():
    ranked = [("a.py", 0.9), ("b.py", 0.7), ("c.py", 0.2)]
    assert recall_at_k(ranked, {"a.py", "c.py"}, k=2) == 0.5
    assert mean_reciprocal_rank(ranked, {"c.py"}) == pytest.approx(1 / 3)


def test_calibration_ece_perfect():
    pairs = [(0.9, 1), (0.1, 0), (0.8, 1), (0.2, 0)]
    assert calibration_ece(pairs) <= 0.15


def test_batch_evaluator_runs_suite():
    root = Path(__file__).resolve().parents[3]
    suite = load_benchmark(root / "data" / "benchmarks" / "default.json")
    preds = {
        sample.id: {
            "risk_score": sample.ground_truth.risk_score,
            "regression_probability": 1.0 if sample.ground_truth.is_regression else 0.0,
            "ranked_files": [(p, 0.9) for p in sample.ground_truth.affected_files],
        }
        for sample in suite.samples
    }
    report = BatchEvaluator(MetricTargets()).evaluate_suite(suite, preds)
    assert report.aggregate_metrics["count"] == len(suite.samples)
    assert report.aggregate_metrics["precision_at_k"] == 1.0
    assert report.aggregate_metrics["risk_mae"] == 0.0


def test_aggregate_metrics():
    agg = aggregate_metrics([{"f1": 0.8, "risk_rmse": 10.0}, {"f1": 0.6, "risk_rmse": 20.0}])
    assert agg["f1"] == pytest.approx(0.7)
    assert agg["risk_rmse"] == pytest.approx(15.0)
