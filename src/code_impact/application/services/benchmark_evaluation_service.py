"""Run benchmark evaluation using the prediction stack."""

from __future__ import annotations

from uuid import uuid4

from code_impact.domain.entities import GraphSnapshot
from code_impact.domain.services import DiffAnalysisResult
from code_impact.infrastructure.analysis.diff_analysis_service import DiffAnalysisService
from code_impact.ml.evaluation.benchmark_loader import default_benchmark_path, load_benchmark
from code_impact.ml.evaluation.evaluator import BatchEvaluator
from code_impact.ml.evaluation.report_store import EvaluationReportStore
from code_impact.ml.evaluation.types import BenchmarkSuite, EvaluationReport, MetricTargets
from code_impact.ml.inference.mock_gnn_predictor import MockGNNPredictor
from code_impact.ml.risk.classical_risk_classifier import ClassicalRiskClassifier
from code_impact.ml.risk.ensemble_fusion import EnsembleFusionService


class BenchmarkEvaluationService:
    """Generates predictions for benchmark samples and scores against ground truth."""

    def __init__(
        self,
        report_store: EvaluationReportStore,
        *,
        targets: MetricTargets | None = None,
        benchmark_dir: str | None = None,
    ) -> None:
        self._store = report_store
        self._targets = targets or MetricTargets()
        self._benchmark_dir = benchmark_dir
        self._diff_service = DiffAnalysisService()
        self._gnn = MockGNNPredictor()
        self._classical = ClassicalRiskClassifier()
        self._ensemble = EnsembleFusionService()
        self._evaluator = BatchEvaluator(self._targets)

    async def run_named_benchmark(self, name: str = "default") -> EvaluationReport:
        base = self._benchmark_dir or "data/benchmarks"
        path = default_benchmark_path(base) if name == "default" else f"{base}/{name}.json"
        suite = load_benchmark(path)
        return await self.run_suite(suite)

    async def run_suite(self, suite: BenchmarkSuite) -> EvaluationReport:
        predictions: dict[str, dict] = {}
        for sample in suite.samples:
            predictions[sample.id] = await self._predict_sample(sample.diff)

        report = self._evaluator.evaluate_suite(suite, predictions)
        self._store.save(report)
        return report

    async def _predict_sample(self, diff: str) -> dict:
        enriched = await self._diff_service.analyze(diff)
        diff_result = DiffAnalysisResult(
            changed_files=enriched.changed_files,
            added_lines=enriched.added_lines,
            deleted_lines=enriched.deleted_lines,
            modified_functions=enriched.modified_functions,
            renamed_files=enriched.renamed_files,
            complexity_delta=enriched.complexity_delta,
            deleted_code_ratio=enriched.deleted_code_ratio,
            raw_diff=enriched.raw_diff,
        )
        empty_graph = GraphSnapshot(
            id=uuid4(),
            repository_id=uuid4(),
            commit_sha="benchmark",
            node_count=0,
            edge_count=0,
            storage_path="",
        )
        gnn_result = await self._gnn.predict(empty_graph, diff_result, None)
        classical_result = self._classical.predict(diff_result, [])
        fused = self._ensemble.fuse(gnn_result, classical_result, [])

        ranked_files = [(f.file_path, f.break_probability) for f in fused.affected_files]
        if not ranked_files:
            ranked_files = [(p, 0.5) for p in diff_result.changed_files]

        return {
            "risk_score": fused.risk_score.value,
            "regression_probability": fused.regression_probability.value,
            "ranked_files": ranked_files,
        }

    def get_report(self, report_id) -> EvaluationReport | None:
        return self._store.get(report_id)

    def list_reports(self, limit: int = 20) -> list[EvaluationReport]:
        return self._store.list_reports(limit=limit)

    @staticmethod
    def targets() -> MetricTargets:
        return MetricTargets()
