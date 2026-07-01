"""Training data types."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from code_impact.domain.entities import GraphSnapshot

if TYPE_CHECKING:
    from torch import Tensor


@dataclass
class TrainingLabels:
    risk_score: float
    is_regression: float
    affected_files: list[str] = field(default_factory=list)


@dataclass
class TrainingSample:
    diff: str
    changed_files: list[str]
    previous_commit_sha: str
    next_commit_sha: str
    graph_snapshot: GraphSnapshot
    labels: TrainingLabels
    is_rollback: bool = False
    issue_ids: list[str] = field(default_factory=list)
    historical_embedding: list[float] | None = None
