"""Offline training dataset assembly from repository history."""

from __future__ import annotations

from uuid import UUID

from code_impact.domain.entities import Commit, GraphSnapshot
from code_impact.domain.repositories import ICommitRepository, IGraphRepository
from code_impact.domain.services import DiffAnalysisResult, IEmbeddingService, IGitService
from code_impact.ml.training.label_extractor import LabelExtractor
from code_impact.ml.training.types import TrainingSample


class TrainingDatasetBuilder:
    """Build labeled training samples from synced repository data."""

    def __init__(
        self,
        git_service: IGitService,
        commit_repo: ICommitRepository,
        graph_repo: IGraphRepository,
        embedding_service: IEmbeddingService | None = None,
        label_extractor: LabelExtractor | None = None,
    ) -> None:
        self._git = git_service
        self._commits = commit_repo
        self._graphs = graph_repo
        self._embeddings = embedding_service
        self._labels = label_extractor or LabelExtractor()

    async def build_for_repository(
        self,
        repository_id: UUID,
        limit: int = 200,
    ) -> list[TrainingSample]:
        commits = await self._commits.list_by_repository(repository_id, limit=limit)
        if len(commits) < 2:
            return []

        regression_commits = [c for c in commits if c.is_regression]
        samples: list[TrainingSample] = []

        for commit in commits:
            if self._labels.is_rollback(commit):
                continue
            parent_sha = commit.metadata.get("parent_sha")
            if not parent_sha:
                continue
            graph = await self._graphs.get_snapshot_by_sha(repository_id, parent_sha)
            if not graph or not graph.nodes:
                continue

            diff_text = await self._safe_diff(repository_id, parent_sha, commit.sha)
            if not diff_text:
                continue

            diff_result = self._minimal_diff_result(diff_text)
            hist = None
            if self._embeddings:
                hist = await self._embeddings.embed_text(diff_text[:4000])

            samples.append(
                self._labels.build_sample(
                    commit=commit,
                    parent_sha=parent_sha,
                    graph_snapshot=graph,
                    diff_result=diff_result,
                    fix_commits=regression_commits,
                    historical_embedding=hist,
                )
            )

        return self._balance_samples(samples)

    async def _safe_diff(self, repository_id: UUID, parent_sha: str, commit_sha: str) -> str:
        try:
            return await self._git.get_diff(repository_id, parent_sha, commit_sha)
        except Exception:
            return ""

    @staticmethod
    def _minimal_diff_result(diff_text: str) -> DiffAnalysisResult:
        files = [
            line.split("+++ b/")[-1].strip()
            for line in diff_text.splitlines()
            if line.startswith("+++ b/")
        ]
        added = sum(1 for line in diff_text.splitlines() if line.startswith("+") and not line.startswith("+++"))
        deleted = sum(1 for line in diff_text.splitlines() if line.startswith("-") and not line.startswith("---"))
        return DiffAnalysisResult(
            changed_files=files,
            added_lines=added,
            deleted_lines=deleted,
            modified_functions=[],
            renamed_files={},
            complexity_delta=0.0,
            deleted_code_ratio=deleted / max(added + deleted, 1),
            raw_diff=diff_text,
        )

    @staticmethod
    def _balance_samples(samples: list[TrainingSample], negative_ratio: float = 3.0) -> list[TrainingSample]:
        positives = [s for s in samples if s.labels.is_regression >= 0.5]
        negatives = [s for s in samples if s.labels.is_regression < 0.5]
        if not positives:
            return samples
        max_negatives = int(len(positives) * negative_ratio)
        return positives + negatives[:max_negatives]
