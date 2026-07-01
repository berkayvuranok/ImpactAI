"""Prediction-related use cases."""

from dataclasses import dataclass
from uuid import UUID

from code_impact.application.services.prediction_pipeline_service import PredictionPipelineService
from code_impact.domain.entities import Prediction
from code_impact.domain.exceptions import EntityNotFoundError
from code_impact.domain.repositories import IPredictionRepository, IRepositoryRepository
from code_impact.domain.value_objects.enums import PredictionStatus


@dataclass
class GetPredictionHistoryQuery:
    repository_id: UUID
    limit: int = 50
    offset: int = 0


class RunPredictionPipelineUseCase:
    def __init__(self, pipeline: PredictionPipelineService) -> None:
        self._pipeline = pipeline

    async def execute(self, prediction_id: UUID) -> Prediction:
        return await self._pipeline.run(prediction_id)


class GetPredictionHistoryUseCase:
    def __init__(self, prediction_repo: IPredictionRepository) -> None:
        self._predictions = prediction_repo

    async def execute(self, query: GetPredictionHistoryQuery) -> tuple[list[Prediction], int]:
        items = await self._predictions.list_by_repository(
            query.repository_id,
            limit=query.limit,
            offset=query.offset,
        )
        total = await self._predictions.count_by_repository(query.repository_id)
        return items, total


class GetRiskSummaryUseCase:
    def __init__(self, prediction_repo: IPredictionRepository) -> None:
        self._predictions = prediction_repo

    async def execute(self, repository_id: UUID) -> dict:
        completed = await self._predictions.list_by_repository(
            repository_id,
            status=PredictionStatus.COMPLETED,
            limit=500,
        )
        if not completed:
            return {
                "repository_id": repository_id,
                "average_risk_score": 0.0,
                "high_risk_predictions": 0,
                "total_predictions": 0,
                "trend": [],
            }

        scores = [p.risk_score.value for p in completed if p.risk_score]
        avg = sum(scores) / len(scores) if scores else 0.0
        high_risk = sum(1 for s in scores if s >= 75.0)
        trend = [
            {
                "prediction_id": str(p.id),
                "risk_score": p.risk_score.value if p.risk_score else 0.0,
                "created_at": p.created_at.isoformat(),
            }
            for p in completed[:20]
        ]
        total = await self._predictions.count_by_repository(repository_id)
        return {
            "repository_id": repository_id,
            "average_risk_score": round(avg, 2),
            "high_risk_predictions": high_risk,
            "total_predictions": total,
            "trend": trend,
        }
