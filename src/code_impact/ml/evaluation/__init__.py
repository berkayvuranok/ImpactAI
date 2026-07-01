"""Model evaluation framework."""

from code_impact.ml.evaluation.benchmark_loader import default_benchmark_path, load_benchmark
from code_impact.ml.evaluation.evaluator import BatchEvaluator
from code_impact.ml.evaluation.metrics import (
    aggregate_metrics,
    calibration_ece,
    compute_metrics,
    mean_reciprocal_rank,
    precision_at_k,
    recall_at_k,
)
from code_impact.ml.evaluation.report_store import EvaluationReportStore
from code_impact.ml.evaluation.types import (
    BenchmarkSample,
    BenchmarkSuite,
    EvaluationReport,
    GroundTruth,
    MetricTargets,
    SampleEvaluation,
)

__all__ = [
    "BatchEvaluator",
    "BenchmarkSample",
    "BenchmarkSuite",
    "EvaluationReport",
    "EvaluationReportStore",
    "GroundTruth",
    "MetricTargets",
    "SampleEvaluation",
    "aggregate_metrics",
    "calibration_ece",
    "compute_metrics",
    "default_benchmark_path",
    "load_benchmark",
    "mean_reciprocal_rank",
    "precision_at_k",
    "recall_at_k",
]
