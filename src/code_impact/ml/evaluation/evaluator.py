"""Batch evaluation against ground-truth benchmarks."""

from __future__ import annotations

from code_impact.ml.evaluation.metrics import aggregate_metrics, compute_metrics
from code_impact.ml.evaluation.types import (
    BenchmarkSample,
    BenchmarkSuite,
    EvaluationReport,
    MetricTargets,
    SampleEvaluation,
)


class BatchEvaluator:
    """Compare model predictions to labeled benchmark samples."""

    def __init__(self, targets: MetricTargets | None = None, *, top_k: int = 5) -> None:
        self._targets = targets or MetricTargets()
        self._top_k = top_k

    def evaluate_suite(
        self,
        suite: BenchmarkSuite,
        predictions_by_sample: dict[str, dict],
    ) -> EvaluationReport:
        sample_results: list[SampleEvaluation] = []
        per_sample_metrics: list[dict[str, float]] = []

        for sample in suite.samples:
            pred = predictions_by_sample.get(sample.id)
            if pred is None:
                continue
            metrics = self.evaluate_single(sample, pred)
            per_sample_metrics.append(metrics)
            sample_results.append(
                SampleEvaluation(
                    sample_id=sample.id,
                    description=sample.description,
                    metrics=metrics,
                    passed=_sample_passed(metrics, self._targets),
                )
            )

        aggregate = aggregate_metrics(per_sample_metrics)
        return EvaluationReport.create(
            benchmark_name=suite.name,
            aggregate_metrics=aggregate,
            targets=self._targets,
            sample_results=sample_results,
            metadata={"description": suite.description, "top_k": self._top_k},
        )

    def evaluate_single(self, sample: BenchmarkSample, prediction: dict) -> dict[str, float]:
        label = {
            "risk_score": sample.ground_truth.risk_score,
            "is_regression": 1.0 if sample.ground_truth.is_regression else 0.0,
            "affected_files": sample.ground_truth.affected_files,
        }
        return compute_metrics([prediction], [label], k=self._top_k)


def _sample_passed(metrics: dict[str, float], targets: MetricTargets) -> bool:
    return (
        metrics.get("f1", 0.0) >= targets.f1 * 0.8
        and metrics.get("risk_mae", 999.0) <= targets.risk_rmse
    )
