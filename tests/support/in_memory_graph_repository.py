"""In-memory graph repository for tests."""

from uuid import UUID

from code_impact.domain.entities import GraphSnapshot
from code_impact.domain.repositories import IGraphRepository


class InMemoryGraphRepository(IGraphRepository):
    def __init__(self) -> None:
        self._snapshots: list[GraphSnapshot] = []

    async def get_latest_snapshot(self, repository_id: UUID) -> GraphSnapshot | None:
        matches = [s for s in self._snapshots if s.repository_id == repository_id]
        if not matches:
            return None
        return sorted(matches, key=lambda s: s.created_at, reverse=True)[0]

    async def get_snapshot_by_sha(
        self, repository_id: UUID, commit_sha: str
    ) -> GraphSnapshot | None:
        return next(
            (
                s
                for s in self._snapshots
                if s.repository_id == repository_id and s.commit_sha.startswith(commit_sha)
            ),
            None,
        )

    async def save_snapshot(self, snapshot: GraphSnapshot) -> GraphSnapshot:
        self._snapshots = [
            s
            for s in self._snapshots
            if not (
                s.repository_id == snapshot.repository_id
                and s.commit_sha == snapshot.commit_sha
            )
        ]
        self._snapshots.append(snapshot)
        return snapshot
