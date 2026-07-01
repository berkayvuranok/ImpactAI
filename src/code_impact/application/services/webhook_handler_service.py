"""Handle webhook events and queue predictions."""

from __future__ import annotations

from uuid import UUID

from code_impact.application.services.webhook_service import WebhookEvent
from code_impact.application.use_cases import PredictImpactCommand, PredictImpactUseCase
from code_impact.domain.exceptions import EntityNotFoundError
from code_impact.domain.repositories import IRepositoryRepository
from code_impact.infrastructure.queue.task_dispatcher import ITaskDispatcher


class WebhookHandlerService:
    def __init__(
        self,
        repository_repo: IRepositoryRepository,
        predict_use_case: PredictImpactUseCase,
        task_dispatcher: ITaskDispatcher,
    ) -> None:
        self._repos = repository_repo
        self._predict = predict_use_case
        self._dispatcher = task_dispatcher

    async def handle(self, event: WebhookEvent, owner_id: UUID) -> UUID:
        repository = await self._repos.find_by_normalized_url(event.repository_url)
        if not repository:
            raise EntityNotFoundError("Repository", event.repository_url)

        prediction = await self._predict.execute(
            PredictImpactCommand(
                repository_id=repository.id,
                created_by=owner_id,
                diff=event.diff,
                base_sha=event.base_sha,
                head_sha=event.head_sha,
                pull_request_id=None,
            )
        )
        self._dispatcher.dispatch_run_prediction(str(prediction.id))
        return prediction.id
