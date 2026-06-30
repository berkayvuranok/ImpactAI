"""SQLAlchemy repository implementations."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from code_impact.domain.entities import Commit, EmbeddingRecord, GraphSnapshot, Issue, Repository, SyncJob, User
from code_impact.domain.repositories import (
    ICommitRepository,
    IEmbeddingRepository,
    IGraphRepository,
    IIssueRepository,
    IRepositoryRepository,
    ISyncJobRepository,
    IUserRepository,
)
from code_impact.infrastructure.persistence import mappers
from code_impact.infrastructure.persistence.models import (
    CommitModel,
    EmbeddingModel,
    GraphEdgeModel,
    GraphNodeModel,
    GraphSnapshotModel,
    IssueModel,
    RepositoryModel,
    SyncJobModel,
    UserModel,
)


class SqlAlchemyUserRepository(IUserRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, user_id: UUID) -> User | None:
        model = await self._session.get(UserModel, user_id)
        return mappers.user_to_domain(model) if model else None

    async def get_by_email(self, email: str) -> User | None:
        result = await self._session.execute(select(UserModel).where(UserModel.email == email))
        model = result.scalar_one_or_none()
        return mappers.user_to_domain(model) if model else None

    async def create(self, user: User) -> User:
        model = mappers.user_to_model(user)
        self._session.add(model)
        await self._session.flush()
        return mappers.user_to_domain(model)


class SqlAlchemyRepositoryRepository(IRepositoryRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, repository_id: UUID) -> Repository | None:
        model = await self._session.get(RepositoryModel, repository_id)
        return mappers.repository_to_domain(model) if model else None

    async def get_by_url(self, url: str) -> Repository | None:
        result = await self._session.execute(select(RepositoryModel).where(RepositoryModel.url == url))
        model = result.scalar_one_or_none()
        return mappers.repository_to_domain(model) if model else None

    async def list_by_owner(self, owner_id: UUID) -> list[Repository]:
        result = await self._session.execute(
            select(RepositoryModel).where(RepositoryModel.owner_id == owner_id)
        )
        return [mappers.repository_to_domain(m) for m in result.scalars()]

    async def create(self, repository: Repository) -> Repository:
        model = mappers.repository_to_model(repository)
        self._session.add(model)
        await self._session.flush()
        return mappers.repository_to_domain(model)

    async def update(self, repository: Repository) -> Repository:
        model = await self._session.get(RepositoryModel, repository.id)
        if not model:
            return repository
        model.name = repository.name
        model.default_branch = repository.default_branch
        model.settings = repository.settings
        model.last_synced_at = repository.last_synced_at
        await self._session.flush()
        return mappers.repository_to_domain(model)


class SqlAlchemyCommitRepository(ICommitRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_sha(self, repository_id: UUID, sha: str) -> Commit | None:
        result = await self._session.execute(
            select(CommitModel).where(
                CommitModel.repository_id == repository_id,
                CommitModel.sha.startswith(sha),
            )
        )
        model = result.scalar_one_or_none()
        return mappers.commit_to_domain(model) if model else None

    async def list_by_repository(
        self, repository_id: UUID, limit: int = 100, offset: int = 0
    ) -> list[Commit]:
        result = await self._session.execute(
            select(CommitModel)
            .where(CommitModel.repository_id == repository_id)
            .order_by(CommitModel.committed_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return [mappers.commit_to_domain(m) for m in result.scalars()]

    async def create_batch(self, commits: list[Commit]) -> list[Commit]:
        models = [mappers.commit_to_model(c) for c in commits]
        self._session.add_all(models)
        await self._session.flush()
        return [mappers.commit_to_domain(m) for m in models]


class SqlAlchemySyncJobRepository(ISyncJobRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, job_id: UUID) -> SyncJob | None:
        model = await self._session.get(SyncJobModel, job_id)
        return mappers.sync_job_to_domain(model) if model else None

    async def create(self, job: SyncJob) -> SyncJob:
        model = mappers.sync_job_to_model(job)
        self._session.add(model)
        await self._session.flush()
        return mappers.sync_job_to_domain(model)

    async def update(self, job: SyncJob) -> SyncJob:
        model = await self._session.get(SyncJobModel, job.id)
        if not model:
            return job
        model.status = job.status.value
        model.started_at = job.started_at
        model.completed_at = job.completed_at
        model.error_message = job.error_message
        model.stats = job.stats
        await self._session.flush()
        return mappers.sync_job_to_domain(model)


class SqlAlchemyGraphRepository(IGraphRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_latest_snapshot(self, repository_id: UUID) -> GraphSnapshot | None:
        result = await self._session.execute(
            select(GraphSnapshotModel)
            .where(GraphSnapshotModel.repository_id == repository_id)
            .order_by(GraphSnapshotModel.created_at.desc())
            .limit(1)
        )
        model = result.scalar_one_or_none()
        if not model:
            return None
        return await self._load_full_snapshot(model)

    async def get_snapshot_by_sha(
        self, repository_id: UUID, commit_sha: str
    ) -> GraphSnapshot | None:
        result = await self._session.execute(
            select(GraphSnapshotModel).where(
                GraphSnapshotModel.repository_id == repository_id,
                GraphSnapshotModel.commit_sha.startswith(commit_sha),
            )
        )
        model = result.scalar_one_or_none()
        if not model:
            return None
        return await self._load_full_snapshot(model)

    async def save_snapshot(self, snapshot: GraphSnapshot) -> GraphSnapshot:
        existing = await self.get_snapshot_by_sha(snapshot.repository_id, snapshot.commit_sha)
        if existing:
            await self._delete_snapshot(existing.id)

        model = mappers.graph_snapshot_to_model(snapshot)
        self._session.add(model)
        await self._session.flush()

        if snapshot.nodes:
            self._session.add_all([mappers.graph_node_to_model(n) for n in snapshot.nodes])
        if snapshot.edges:
            self._session.add_all([mappers.graph_edge_to_model(e) for e in snapshot.edges])
        await self._session.flush()
        return snapshot

    async def _load_full_snapshot(self, model: GraphSnapshotModel) -> GraphSnapshot:
        nodes_result = await self._session.execute(
            select(GraphNodeModel).where(GraphNodeModel.snapshot_id == model.id)
        )
        edges_result = await self._session.execute(
            select(GraphEdgeModel).where(GraphEdgeModel.snapshot_id == model.id)
        )
        nodes = [mappers.graph_node_to_domain(n) for n in nodes_result.scalars()]
        edges = [mappers.graph_edge_to_domain(e) for e in edges_result.scalars()]
        return mappers.graph_snapshot_to_domain(model, nodes=nodes, edges=edges)

    async def _delete_snapshot(self, snapshot_id: UUID) -> None:
        await self._session.execute(
            GraphEdgeModel.__table__.delete().where(GraphEdgeModel.snapshot_id == snapshot_id)
        )
        await self._session.execute(
            GraphNodeModel.__table__.delete().where(GraphNodeModel.snapshot_id == snapshot_id)
        )
        await self._session.execute(
            GraphSnapshotModel.__table__.delete().where(GraphSnapshotModel.id == snapshot_id)
        )
        await self._session.flush()


class SqlAlchemyIssueRepository(IIssueRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_by_repository(
        self, repository_id: UUID, limit: int = 500, offset: int = 0
    ) -> list[Issue]:
        result = await self._session.execute(
            select(IssueModel)
            .where(IssueModel.repository_id == repository_id)
            .limit(limit)
            .offset(offset)
        )
        return [mappers.issue_to_domain(m) for m in result.scalars()]

    async def create_batch(self, issues: list[Issue]) -> list[Issue]:
        models = [mappers.issue_to_model(i) for i in issues]
        self._session.add_all(models)
        await self._session.flush()
        return [mappers.issue_to_domain(m) for m in models]


class SqlAlchemyEmbeddingRepository(IEmbeddingRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_entity(
        self, repository_id: UUID, entity_type: str, entity_id: UUID
    ) -> EmbeddingRecord | None:
        result = await self._session.execute(
            select(EmbeddingModel).where(
                EmbeddingModel.repository_id == repository_id,
                EmbeddingModel.entity_type == entity_type,
                EmbeddingModel.entity_id == entity_id,
            )
        )
        model = result.scalar_one_or_none()
        return mappers.embedding_to_domain(model) if model else None

    async def list_by_repository(
        self, repository_id: UUID, entity_type: str | None = None
    ) -> list[EmbeddingRecord]:
        query = select(EmbeddingModel).where(EmbeddingModel.repository_id == repository_id)
        if entity_type:
            query = query.where(EmbeddingModel.entity_type == entity_type)
        result = await self._session.execute(query)
        return [mappers.embedding_to_domain(m) for m in result.scalars()]

    async def create(self, record: EmbeddingRecord) -> EmbeddingRecord:
        model = mappers.embedding_to_model(record)
        self._session.add(model)
        await self._session.flush()
        return mappers.embedding_to_domain(model)

    async def create_batch(self, records: list[EmbeddingRecord]) -> list[EmbeddingRecord]:
        models = [mappers.embedding_to_model(r) for r in records]
        self._session.add_all(models)
        await self._session.flush()
        return [mappers.embedding_to_domain(m) for m in models]
