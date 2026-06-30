"""Prediction endpoints."""

from uuid import UUID, uuid4

from fastapi import APIRouter, HTTPException, status

from code_impact.application.schemas import (
    PredictAcceptedResponse,
    PredictRequest,
    PredictionHistoryResponse,
    PredictionResponse,
    RiskSummaryResponse,
)

router = APIRouter()


@router.post("/predict", response_model=PredictAcceptedResponse, status_code=status.HTTP_202_ACCEPTED)
async def predict_impact(body: PredictRequest) -> PredictAcceptedResponse:
    """
    Submit a diff for impact prediction.

    Returns immediately with prediction_id. Poll GET /prediction/{id} for results.
    ML pipeline (GNN + embeddings) runs async via Celery worker.
    """
    prediction_id = uuid4()
    return PredictAcceptedResponse(
        prediction_id=prediction_id,
        status="pending",
        message="Prediction pipeline queued — full implementation in Steps 5-8",
    )


@router.get("/prediction/{prediction_id}", response_model=PredictionResponse)
async def get_prediction(prediction_id: UUID) -> PredictionResponse:
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail=f"Prediction {prediction_id} — full implementation in Step 8",
    )


@router.get("/history/{repository_id}", response_model=PredictionHistoryResponse)
async def get_prediction_history(
    repository_id: UUID,
    limit: int = 50,
    offset: int = 0,
) -> PredictionHistoryResponse:
    return PredictionHistoryResponse(items=[], total=0, limit=limit, offset=offset)


@router.get("/risk/{repository_id}", response_model=RiskSummaryResponse)
async def get_risk_summary(repository_id: UUID) -> RiskSummaryResponse:
    return RiskSummaryResponse(
        repository_id=repository_id,
        average_risk_score=0.0,
        high_risk_predictions=0,
        total_predictions=0,
        trend=[],
    )
