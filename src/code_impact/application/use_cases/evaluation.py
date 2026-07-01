"""Evaluation use cases."""

from __future__ import annotations

from uuid import UUID

from code_impact.application.services.benchmark_evaluation_service import BenchmarkEvaluationService
from code_impact.domain.exceptions import EntityNotFoundError
from code_impact.ml.evaluation.types import EvaluationReport, MetricTargets


class RunBenchmarkEvaluationUseCase:
    def __init__(self, service: BenchmarkEvaluationService) -> None:
        self._service = service

    async def execute(self, benchmark_name: str = "default") -> EvaluationReport:
        return await self._service.run_named_benchmark(benchmark_name)


class GetEvaluationReportUseCase:
    def __init__(self, service: BenchmarkEvaluationService) -> None:
        self._service = service

    async def execute(self, report_id: UUID) -> EvaluationReport:
        report = self._service.get_report(report_id)
        if not report:
            raise EntityNotFoundError("EvaluationReport", report_id)
        return report


class ListEvaluationReportsUseCase:
    def __init__(self, service: BenchmarkEvaluationService) -> None:
        self._service = service

    async def execute(self, limit: int = 20) -> list[EvaluationReport]:
        return self._service.list_reports(limit=limit)


class GetMetricTargetsUseCase:
    @staticmethod
    async def execute() -> MetricTargets:
        return BenchmarkEvaluationService.targets()
