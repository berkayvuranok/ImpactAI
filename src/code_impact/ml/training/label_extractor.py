"""Extract regression / rollback labels from commit history."""

from __future__ import annotations

import re
from datetime import UTC, datetime, timedelta

from code_impact.domain.entities import Commit, GraphSnapshot
from code_impact.domain.services import DiffAnalysisResult
from code_impact.ml.training.types import TrainingLabels, TrainingSample

REVERT_PATTERN = re.compile(r"\brevert\b", re.IGNORECASE)


class LabelExtractor:
    """Heuristic label extraction from Git history and issue metadata."""

    def __init__(self, regression_window_days: int = 14) -> None:
        self._window = regression_window_days

    def is_rollback(self, commit: Commit) -> bool:
        if commit.is_rollback:
            return True
        return bool(REVERT_PATTERN.search(commit.message))

    def extract_labels(
        self,
        commit: Commit,
        fix_commits: list[Commit],
        diff_result: DiffAnalysisResult,
    ) -> TrainingLabels:
        is_regression = commit.is_regression or self._has_linked_fix(commit, fix_commits)
        affected = self._affected_files(commit, fix_commits, diff_result)
        risk = self._risk_score(commit, diff_result, is_regression)
        return TrainingLabels(
            risk_score=risk,
            is_regression=1.0 if is_regression else 0.0,
            affected_files=affected,
        )

    def build_sample(
        self,
        commit: Commit,
        parent_sha: str,
        graph_snapshot: GraphSnapshot,
        diff_result: DiffAnalysisResult,
        fix_commits: list[Commit],
        historical_embedding: list[float] | None = None,
    ) -> TrainingSample:
        labels = self.extract_labels(commit, fix_commits, diff_result)
        return TrainingSample(
            diff=diff_result.raw_diff,
            changed_files=diff_result.changed_files,
            previous_commit_sha=parent_sha,
            next_commit_sha=commit.sha,
            graph_snapshot=graph_snapshot,
            labels=labels,
            is_rollback=self.is_rollback(commit),
            historical_embedding=historical_embedding,
        )

    def _has_linked_fix(self, commit: Commit, fix_commits: list[Commit]) -> bool:
        commit_time = commit.committed_at
        if commit_time.tzinfo is None:
            commit_time = commit_time.replace(tzinfo=UTC)
        window_end = commit_time + timedelta(days=self._window)
        for fix in fix_commits:
            fix_time = fix.committed_at
            if fix_time.tzinfo is None:
                fix_time = fix_time.replace(tzinfo=UTC)
            if commit_time < fix_time <= window_end:
                linked = fix.metadata.get("fixes_commit_sha") or fix.metadata.get("linked_commit_sha")
                if linked and str(linked).startswith(commit.sha[:8]):
                    return True
                if commit.sha[:8] in fix.message:
                    return True
        return False

    def _affected_files(
        self,
        commit: Commit,
        fix_commits: list[Commit],
        diff_result: DiffAnalysisResult,
    ) -> list[str]:
        changed = set(diff_result.changed_files)
        affected: set[str] = set()
        for fix in fix_commits:
            fix_files = fix.metadata.get("changed_files", [])
            for path in fix_files:
                if path not in changed:
                    affected.add(path)
        if not affected and diff_result.changed_files:
            # Fallback: neighbors in diff are the directly changed files
            affected.update(diff_result.changed_files[:3])
        return sorted(affected)

    @staticmethod
    def _risk_score(commit: Commit, diff_result: DiffAnalysisResult, is_regression: bool) -> float:
        base = min(
            20.0
            + diff_result.added_lines * 0.05
            + diff_result.deleted_lines * 0.08
            + abs(diff_result.complexity_delta) * 2.0
            + len(diff_result.changed_files) * 3.0,
            85.0,
        )
        if is_regression:
            base = min(base + 25.0, 100.0)
        if commit.is_rollback:
            base = min(base + 15.0, 100.0)
        return base
