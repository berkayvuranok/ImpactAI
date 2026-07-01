"""Evaluation framework endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from code_impact.application.schemas import (
    EvaluationReportListResponse,
    EvaluationReportResponse,
    MetricTargetsResponse,
    RunBenchmarkRequest,
    SampleEvaluationResponse,
)
from code_impact.application.use_cases.evaluation import (
    GetEvaluationReportUseCase,
    GetMetricTargetsUseCase,
    ListEvaluationReportsUseCase,
    RunBenchmarkEvaluationUseCase,
)
from code_impact.domain.exceptions import EntityNotFoundError
from code_impact.ml.evaluation.types import EvaluationReport
from code_impact.presentation.api.dependencies import (
    get_get_evaluation_report_use_case,
    get_get_metric_targets_use_case,
    get_list_evaluation_reports_use_case,
    get_run_benchmark_evaluation_use_case,
)

router = APIRouter(prefix="/evaluate")


def _to_response(report: EvaluationReport) -> EvaluationReportResponse:
    return EvaluationReportResponse(
        id=report.id,
        benchmark_name=report.benchmark_name,
        created_at=report.created_at,
        aggregate_metrics=report.aggregate_metrics,
        targets=report.targets,
        passed=report.passed,
        sample_results=[
            SampleEvaluationResponse(
                sample_id=s.sample_id,
                description=s.description,
                metrics=s.metrics,
                passed=s.passed,
            )
            for s in report.sample_results
        ],
        metadata=report.metadata,
    )


@router.get("/targets", response_model=MetricTargetsResponse)
async def get_metric_targets(
    use_case: GetMetricTargetsUseCase = Depends(get_get_metric_targets_use_case),
) -> MetricTargetsResponse:
    targets = await use_case.execute()
    return MetricTargetsResponse(**targets.to_dict())


@router.post("/benchmark", response_model=EvaluationReportResponse)
async def run_benchmark_evaluation(
    body: RunBenchmarkRequest,
    use_case: RunBenchmarkEvaluationUseCase = Depends(get_run_benchmark_evaluation_use_case),
) -> EvaluationReportResponse:
    report = await use_case.execute(body.benchmark_name)
    return _to_response(report)


@router.get("/reports", response_model=EvaluationReportListResponse)
async def list_evaluation_reports(
    limit: int = 20,
    use_case: ListEvaluationReportsUseCase = Depends(get_list_evaluation_reports_use_case),
) -> EvaluationReportListResponse:
    reports = await use_case.execute(limit=limit)
    items = [_to_response(r) for r in reports]
    return EvaluationReportListResponse(items=items, total=len(items))


@router.get("/report/{report_id}", response_model=EvaluationReportResponse)
async def get_evaluation_report(
    report_id: UUID,
    use_case: GetEvaluationReportUseCase = Depends(get_get_evaluation_report_use_case),
) -> EvaluationReportResponse:
    try:
        report = await use_case.execute(report_id)
    except EntityNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return _to_response(report)
