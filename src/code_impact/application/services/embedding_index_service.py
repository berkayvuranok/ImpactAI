"""Build and index embeddings for commits, issues, and files."""

from __future__ import annotations

from uuid import UUID, uuid4

from code_impact.domain.entities import Commit, EmbeddingRecord, Issue
from code_impact.domain.repositories import (
    ICommitRepository,
    IEmbeddingRepository,
    IIssueRepository,
)
from code_impact.domain.services import IEmbeddingService
from code_impact.domain.services.git_service import IGitService
from code_impact.domain.services.vector_store import IVectorStore, VectorPoint
from code_impact.domain.value_objects.enums import EmbeddingEntityType
from code_impact.infrastructure.config.logging import get_logger
from code_impact.infrastructure.config.settings import Settings

logger = get_logger(__name__)

MAX_DIFF_CHARS = 4000
BATCH_SIZE = 32


class EmbeddingIndexService:
    def __init__(
        self,
        embedding_service: IEmbeddingService,
        vector_store: IVectorStore,
        embedding_repo: IEmbeddingRepository,
        commit_repo: ICommitRepository,
        issue_repo: IIssueRepository,
        git_service: IGitService,
        settings: Settings,
    ) -> None:
        self._embeddings = embedding_service
        self._store = vector_store
        self._embedding_repo = embedding_repo
        self._commit_repo = commit_repo
        self._issue_repo = issue_repo
        self._git = git_service
        self._settings = settings

    async def index_repository_commits(
        self,
        repository_id: UUID,
        *,
        limit: int = 500,
        reindex: bool = False,
    ) -> dict:
        await self._store.ensure_collection(
            self._settings.qdrant_collection_commits,
            self._embeddings.dimension,
        )

        if reindex:
            await self._store.delete_by_filter(
                self._settings.qdrant_collection_commits,
                {"repository_id": str(repository_id)},
            )

        commits = await self._commit_repo.list_by_repository(repository_id, limit=limit)
        indexed = 0
        skipped = 0

        batch_commits: list[Commit] = []
        batch_texts: list[str] = []

        for commit in commits:
            if not reindex:
                existing = await self._embedding_repo.get_by_entity(
                    repository_id,
                    EmbeddingEntityType.COMMIT.value,
                    commit.id,
                )
                if existing:
                    skipped += 1
                    continue

            text = await self._commit_embedding_text(repository_id, commit)
            batch_commits.append(commit)
            batch_texts.append(text)

            if len(batch_commits) >= BATCH_SIZE:
                indexed += await self._flush_commit_batch(repository_id, batch_commits, batch_texts)
                batch_commits, batch_texts = [], []

        if batch_commits:
            indexed += await self._flush_commit_batch(repository_id, batch_commits, batch_texts)

        logger.info(
            "commits_indexed",
            repository_id=str(repository_id),
            indexed=indexed,
            skipped=skipped,
        )
        return {"indexed": indexed, "skipped": skipped, "total": len(commits)}

    async def index_repository_issues(
        self,
        repository_id: UUID,
        *,
        limit: int = 500,
        reindex: bool = False,
    ) -> dict:
        await self._store.ensure_collection(
            self._settings.qdrant_collection_issues,
            self._embeddings.dimension,
        )

        if reindex:
            await self._store.delete_by_filter(
                self._settings.qdrant_collection_issues,
                {"repository_id": str(repository_id)},
            )

        issues = await self._issue_repo.list_by_repository(repository_id, limit=limit)
        indexed = 0
        skipped = 0
        batch_issues: list[Issue] = []
        batch_texts: list[str] = []

        for issue in issues:
            if not reindex:
                existing = await self._embedding_repo.get_by_entity(
                    repository_id,
                    EmbeddingEntityType.ISSUE.value,
                    issue.id,
                )
                if existing:
                    skipped += 1
                    continue

            text = f"{issue.title}\nType: {issue.issue_type}\nState: {issue.state}"
            batch_issues.append(issue)
            batch_texts.append(text)

            if len(batch_issues) >= BATCH_SIZE:
                indexed += await self._flush_issue_batch(repository_id, batch_issues, batch_texts)
                batch_issues, batch_texts = [], []

        if batch_issues:
            indexed += await self._flush_issue_batch(repository_id, batch_issues, batch_texts)

        return {"indexed": indexed, "skipped": skipped, "total": len(issues)}

    async def index_diff(self, repository_id: UUID, diff_text: str) -> list[float]:
        """Embed a diff for online search — returns vector without persisting."""
        return await self._embeddings.embed_text(diff_text[:MAX_DIFF_CHARS])

    async def _commit_embedding_text(self, repository_id: UUID, commit: Commit) -> str:
        parts = [
            f"Commit: {commit.message}",
            f"Author: {commit.author_email}",
            f"Regression: {commit.is_regression}",
            f"Rollback: {commit.is_rollback}",
        ]

        parent_shas = commit.metadata.get("parent_shas", [])
        if parent_shas:
            try:
                diff = await self._git.get_diff(
                    repository_id, parent_shas[0], commit.sha
                )
                parts.append(diff[:MAX_DIFF_CHARS])
            except Exception:
                pass

        return "\n".join(parts)

    async def _flush_commit_batch(
        self,
        repository_id: UUID,
        commits: list[Commit],
        texts: list[str],
    ) -> int:
        vectors = await self._embeddings.embed_batch(texts)
        points: list[VectorPoint] = []
        records: list[EmbeddingRecord] = []

        for commit, vector in zip(commits, vectors, strict=True):
            point_id = str(uuid4())
            points.append(
                VectorPoint(
                    id=point_id,
                    vector=vector,
                    payload={
                        "repository_id": str(repository_id),
                        "commit_sha": commit.sha,
                        "commit_id": str(commit.id),
                        "message": commit.message[:500],
                        "is_regression": commit.is_regression,
                        "is_rollback": commit.is_rollback,
                        "linked_issue_ids": commit.metadata.get("linked_issue_ids", []),
                        "entity_type": EmbeddingEntityType.COMMIT.value,
                    },
                )
            )
            records.append(
                EmbeddingRecord(
                    id=uuid4(),
                    repository_id=repository_id,
                    entity_type=EmbeddingEntityType.COMMIT.value,
                    entity_id=commit.id,
                    model_name=self._embeddings.model_name,
                    dimension=len(vector),
                    qdrant_point_id=point_id,
                )
            )

        await self._store.upsert(self._settings.qdrant_collection_commits, points)
        await self._embedding_repo.create_batch(records)
        return len(commits)

    async def _flush_issue_batch(
        self,
        repository_id: UUID,
        issues: list[Issue],
        texts: list[str],
    ) -> int:
        vectors = await self._embeddings.embed_batch(texts)
        points: list[VectorPoint] = []
        records: list[EmbeddingRecord] = []

        for issue, vector in zip(issues, vectors, strict=True):
            point_id = str(uuid4())
            points.append(
                VectorPoint(
                    id=point_id,
                    vector=vector,
                    payload={
                        "repository_id": str(repository_id),
                        "issue_id": str(issue.id),
                        "external_id": issue.external_id,
                        "title": issue.title[:500],
                        "issue_type": issue.issue_type,
                        "state": issue.state,
                        "entity_type": EmbeddingEntityType.ISSUE.value,
                    },
                )
            )
            records.append(
                EmbeddingRecord(
                    id=uuid4(),
                    repository_id=repository_id,
                    entity_type=EmbeddingEntityType.ISSUE.value,
                    entity_id=issue.id,
                    model_name=self._embeddings.model_name,
                    dimension=len(vector),
                    qdrant_point_id=point_id,
                )
            )

        await self._store.upsert(self._settings.qdrant_collection_issues, points)
        await self._embedding_repo.create_batch(records)
        return len(issues)
