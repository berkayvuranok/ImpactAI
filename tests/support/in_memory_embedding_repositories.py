"""In-memory issue and embedding repositories for tests."""

from uuid import UUID

from code_impact.domain.entities import EmbeddingRecord, Issue
from code_impact.domain.repositories import IEmbeddingRepository, IIssueRepository


class InMemoryIssueRepository(IIssueRepository):
    def __init__(self) -> None:
        self._issues: list[Issue] = []

    async def list_by_repository(
        self, repository_id: UUID, limit: int = 500, offset: int = 0
    ) -> list[Issue]:
        items = [i for i in self._issues if i.repository_id == repository_id]
        return items[offset : offset + limit]

    async def create_batch(self, issues: list[Issue]) -> list[Issue]:
        self._issues.extend(issues)
        return issues


class InMemoryEmbeddingRepository(IEmbeddingRepository):
    def __init__(self) -> None:
        self._records: list[EmbeddingRecord] = []

    async def get_by_entity(
        self, repository_id: UUID, entity_type: str, entity_id: UUID
    ) -> EmbeddingRecord | None:
        return next(
            (
                r
                for r in self._records
                if r.repository_id == repository_id
                and r.entity_type == entity_type
                and r.entity_id == entity_id
            ),
            None,
        )

    async def list_by_repository(
        self, repository_id: UUID, entity_type: str | None = None
    ) -> list[EmbeddingRecord]:
        items = [r for r in self._records if r.repository_id == repository_id]
        if entity_type:
            items = [r for r in items if r.entity_type == entity_type]
        return items

    async def create(self, record: EmbeddingRecord) -> EmbeddingRecord:
        self._records.append(record)
        return record

    async def create_batch(self, records: list[EmbeddingRecord]) -> list[EmbeddingRecord]:
        self._records.extend(records)
        return records
