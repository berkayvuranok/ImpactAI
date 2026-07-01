"""Prediction endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from code_impact.application.schemas import (
    PredictAcceptedResponse,
    PredictRequest,
    PredictionHistoryResponse,
    PredictionResponse,
    RiskSummaryResponse,
)
from code_impact.application.services.prediction_mapper import prediction_to_response
from code_impact.application.use_cases import GetPredictionUseCase, PredictImpactCommand, PredictImpactUseCase
from code_impact.application.use_cases.prediction import (
    GetPredictionHistoryQuery,
    GetPredictionHistoryUseCase,
    GetRiskSummaryUseCase,
)
from code_impact.domain.exceptions import EntityNotFoundError
from code_impact.domain.entities import User
from code_impact.infrastructure.queue.task_dispatcher import ITaskDispatcher
from code_impact.presentation.api.dependencies import (
    get_current_user,
    get_get_prediction_history_use_case,
    get_get_prediction_use_case,
    get_get_risk_summary_use_case,
    get_predict_impact_use_case,
    get_task_dispatcher,
)

router = APIRouter()


@router.post("/predict", response_model=PredictAcceptedResponse, status_code=status.HTTP_202_ACCEPTED)
async def predict_impact(
    body: PredictRequest,
    current_user: User = Depends(get_current_user),
    use_case: PredictImpactUseCase = Depends(get_predict_impact_use_case),
    dispatcher: ITaskDispatcher = Depends(get_task_dispatcher),
) -> PredictAcceptedResponse:
    """Submit a diff for impact prediction. Poll GET /prediction/{id} for results."""
    try:
        prediction = await use_case.execute(
            PredictImpactCommand(
                repository_id=body.repository_id,
                created_by=current_user.id,
                diff=body.diff,
                base_sha=body.base_sha,
                head_sha=body.head_sha,
                pull_request_id=body.pull_request_id,
            )
        )
    except EntityNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    dispatcher.dispatch_run_prediction(str(prediction.id))
    return PredictAcceptedResponse(
        prediction_id=prediction.id,
        status=prediction.status.value,
        message="Prediction pipeline queued",
    )


@router.get("/prediction/{prediction_id}", response_model=PredictionResponse)
async def get_prediction(
    prediction_id: UUID,
    use_case: GetPredictionUseCase = Depends(get_get_prediction_use_case),
) -> PredictionResponse:
    try:
        prediction = await use_case.execute(prediction_id)
    except EntityNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return prediction_to_response(prediction)


@router.get("/history/{repository_id}", response_model=PredictionHistoryResponse)
async def get_prediction_history(
    repository_id: UUID,
    limit: int = 50,
    offset: int = 0,
    use_case: GetPredictionHistoryUseCase = Depends(get_get_prediction_history_use_case),
) -> PredictionHistoryResponse:
    items, total = await use_case.execute(
        GetPredictionHistoryQuery(repository_id=repository_id, limit=limit, offset=offset)
    )
    return PredictionHistoryResponse(
        items=[prediction_to_response(p) for p in items],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/risk/{repository_id}", response_model=RiskSummaryResponse)
async def get_risk_summary(
    repository_id: UUID,
    use_case: GetRiskSummaryUseCase = Depends(get_get_risk_summary_use_case),
) -> RiskSummaryResponse:
    summary = await use_case.execute(repository_id)
    return RiskSummaryResponse(**summary)
