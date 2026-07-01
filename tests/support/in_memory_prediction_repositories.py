"""In-memory prediction and reviewer repositories for tests."""

from uuid import UUID

from code_impact.domain.entities import Prediction, ReviewerProfile
from code_impact.domain.repositories import IPredictionRepository, IReviewerProfileRepository
from code_impact.domain.value_objects.enums import PredictionStatus


class InMemoryPredictionRepository(IPredictionRepository):
    def __init__(self) -> None:
        self._store: dict[UUID, Prediction] = {}

    async def get_by_id(self, prediction_id: UUID) -> Prediction | None:
        return self._store.get(prediction_id)

    async def list_by_repository(
        self,
        repository_id: UUID,
        status: PredictionStatus | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Prediction]:
        items = [p for p in self._store.values() if p.repository_id == repository_id]
        if status:
            items = [p for p in items if p.status == status]
        items.sort(key=lambda p: p.created_at, reverse=True)
        return items[offset : offset + limit]

    async def create(self, prediction: Prediction) -> Prediction:
        self._store[prediction.id] = prediction
        return prediction

    async def update(self, prediction: Prediction) -> Prediction:
        self._store[prediction.id] = prediction
        return prediction

    async def count_by_repository(self, repository_id: UUID) -> int:
        return sum(1 for p in self._store.values() if p.repository_id == repository_id)


class InMemoryReviewerProfileRepository(IReviewerProfileRepository):
    def __init__(self) -> None:
        self._store: list[ReviewerProfile] = []

    async def list_by_repository(self, repository_id: UUID) -> list[ReviewerProfile]:
        return [p for p in self._store if p.repository_id == repository_id]

    async def create_batch(self, profiles: list[ReviewerProfile]) -> list[ReviewerProfile]:
        self._store.extend(profiles)
        return profiles
