"""Evaluation framework types."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID, uuid4


@dataclass(frozen=True, slots=True)
class MetricTargets:
    precision_at_k: float = 0.70
    recall_at_k: float = 0.65
    f1: float = 0.67
    roc_auc: float = 0.85
    risk_rmse: float = 15.0
    mrr: float = 0.60
    calibration_ece: float = 0.05

    def to_dict(self) -> dict[str, float]:
        return {
            "precision_at_k": self.precision_at_k,
            "recall_at_k": self.recall_at_k,
            "f1": self.f1,
            "roc_auc": self.roc_auc,
            "risk_rmse": self.risk_rmse,
            "mrr": self.mrr,
            "calibration_ece": self.calibration_ece,
        }


@dataclass(frozen=True, slots=True)
class GroundTruth:
    risk_score: float
    is_regression: bool
    affected_files: list[str] = field(default_factory=list)


@dataclass(frozen=True, slots=True)
class BenchmarkSample:
    id: str
    description: str
    diff: str
    ground_truth: GroundTruth


@dataclass(frozen=True, slots=True)
class BenchmarkSuite:
    name: str
    description: str
    samples: list[BenchmarkSample]


@dataclass(frozen=True, slots=True)
class SampleEvaluation:
    sample_id: str
    description: str
    metrics: dict[str, float]
    passed: bool


@dataclass
class EvaluationReport:
    id: UUID
    benchmark_name: str
    created_at: datetime
    aggregate_metrics: dict[str, float]
    targets: dict[str, float]
    passed: bool
    sample_results: list[SampleEvaluation]
    metadata: dict = field(default_factory=dict)

    @classmethod
    def create(
        cls,
        benchmark_name: str,
        aggregate_metrics: dict[str, float],
        targets: MetricTargets,
        sample_results: list[SampleEvaluation],
        *,
        metadata: dict | None = None,
    ) -> EvaluationReport:
        passed = _check_targets(aggregate_metrics, targets)
        return cls(
            id=uuid4(),
            benchmark_name=benchmark_name,
            created_at=datetime.now(UTC),
            aggregate_metrics=aggregate_metrics,
            targets=targets.to_dict(),
            passed=passed,
            sample_results=sample_results,
            metadata=metadata or {},
        )

    def to_dict(self) -> dict:
        return {
            "id": str(self.id),
            "benchmark_name": self.benchmark_name,
            "created_at": self.created_at.isoformat(),
            "aggregate_metrics": self.aggregate_metrics,
            "targets": self.targets,
            "passed": self.passed,
            "sample_results": [
                {
                    "sample_id": s.sample_id,
                    "description": s.description,
                    "metrics": s.metrics,
                    "passed": s.passed,
                }
                for s in self.sample_results
            ],
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict) -> EvaluationReport:
        return cls(
            id=UUID(data["id"]),
            benchmark_name=data["benchmark_name"],
            created_at=datetime.fromisoformat(data["created_at"]),
            aggregate_metrics=data["aggregate_metrics"],
            targets=data["targets"],
            passed=data["passed"],
            sample_results=[
                SampleEvaluation(
                    sample_id=s["sample_id"],
                    description=s["description"],
                    metrics=s["metrics"],
                    passed=s["passed"],
                )
                for s in data.get("sample_results", [])
            ],
            metadata=data.get("metadata", {}),
        )


def _check_targets(metrics: dict[str, float], targets: MetricTargets) -> bool:
    checks = [
        metrics.get("precision_at_k", 0.0) >= targets.precision_at_k,
        metrics.get("recall_at_k", 0.0) >= targets.recall_at_k,
        metrics.get("f1", 0.0) >= targets.f1,
        metrics.get("roc_auc_proxy", 0.0) >= targets.roc_auc,
        metrics.get("risk_rmse", 999.0) <= targets.risk_rmse,
        metrics.get("mrr", 0.0) >= targets.mrr,
        metrics.get("calibration_ece", 1.0) <= targets.calibration_ece,
    ]
    return all(checks)
