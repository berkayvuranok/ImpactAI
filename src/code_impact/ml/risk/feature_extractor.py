"""Classical ML feature extraction from diff analysis."""

from __future__ import annotations

from dataclasses import dataclass

from code_impact.domain.entities import SimilarCommit
from code_impact.domain.services import DiffAnalysisResult


@dataclass(frozen=True, slots=True)
class DiffRiskFeatures:
    changed_file_count: float
    added_lines_norm: float
    deleted_lines_norm: float
    complexity_delta_norm: float
    deleted_code_ratio: float
    modified_function_count: float
    rename_count: float
    similar_regression_rate: float
    max_similarity: float
    api_db_mq_surface: float


def extract_risk_features(
    diff_result: DiffAnalysisResult,
    similar_commits: list[SimilarCommit] | None = None,
    *,
    api_db_mq_hits: int = 0,
) -> DiffRiskFeatures:
    similar = similar_commits or []
    regression_hits = sum(1 for c in similar if c.is_regression)
    regression_rate = regression_hits / len(similar) if similar else 0.0
    max_sim = max((c.similarity_score for c in similar), default=0.0)

    total_lines = diff_result.added_lines + diff_result.deleted_lines
    return DiffRiskFeatures(
        changed_file_count=min(len(diff_result.changed_files) / 20.0, 1.0),
        added_lines_norm=min(diff_result.added_lines / 500.0, 1.0),
        deleted_lines_norm=min(diff_result.deleted_lines / 500.0, 1.0),
        complexity_delta_norm=min(abs(diff_result.complexity_delta) / 30.0, 1.0),
        deleted_code_ratio=min(max(diff_result.deleted_code_ratio, 0.0), 1.0),
        modified_function_count=min(len(diff_result.modified_functions) / 25.0, 1.0),
        rename_count=min(len(diff_result.renamed_files) / 10.0, 1.0),
        similar_regression_rate=regression_rate,
        max_similarity=max_sim,
        api_db_mq_surface=min(api_db_mq_hits / 5.0, 1.0),
    )
