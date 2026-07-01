"""Synthetic graph fixtures for ML tests."""

from datetime import UTC, datetime
from uuid import uuid4

from code_impact.domain.entities import Commit, GraphEdge, GraphNode, GraphSnapshot
from code_impact.domain.services import DiffAnalysisResult
from code_impact.domain.value_objects.enums import EdgeType, NodeType
from code_impact.ml.training.types import TrainingLabels, TrainingSample


def sample_graph() -> GraphSnapshot:
    sid = uuid4()
    repo_id = uuid4()
    nodes = [
        GraphNode(uuid4(), sid, "file:a.py", NodeType.FILE, "a.py", "a.py", {"complexity": 5}),
        GraphNode(uuid4(), sid, "file:b.py", NodeType.FILE, "b.py", "b.py", {"complexity": 8}),
        GraphNode(uuid4(), sid, "file:c.py", NodeType.FILE, "c.py", "c.py", {"complexity": 3}),
        GraphNode(uuid4(), sid, "fn:run", NodeType.FUNCTION, "run", "a.py"),
    ]
    edges = [
        GraphEdge(uuid4(), sid, "file:a.py", "file:b.py", EdgeType.IMPORT),
        GraphEdge(uuid4(), sid, "file:b.py", "file:c.py", EdgeType.CALL),
        GraphEdge(uuid4(), sid, "fn:run", "file:b.py", EdgeType.CALL),
    ]
    return GraphSnapshot(
        id=sid,
        repository_id=repo_id,
        commit_sha="abc123",
        node_count=len(nodes),
        edge_count=len(edges),
        storage_path="",
        nodes=nodes,
        edges=edges,
    )


def sample_diff() -> DiffAnalysisResult:
    return DiffAnalysisResult(
        changed_files=["a.py"],
        added_lines=12,
        deleted_lines=3,
        modified_functions=["run"],
        renamed_files={},
        complexity_delta=2.0,
        deleted_code_ratio=0.2,
        raw_diff="diff --git a/a.py b/a.py\n",
    )


def sample_training_sample(is_regression: bool = True) -> TrainingSample:
    graph = sample_graph()
    diff = sample_diff()
    return TrainingSample(
        diff=diff.raw_diff,
        changed_files=diff.changed_files,
        previous_commit_sha="parent",
        next_commit_sha="child",
        graph_snapshot=graph,
        labels=TrainingLabels(
            risk_score=75.0 if is_regression else 25.0,
            is_regression=1.0 if is_regression else 0.0,
            affected_files=["b.py", "c.py"] if is_regression else ["a.py"],
        ),
        historical_embedding=[0.01] * 384,
    )


def sample_commit(is_regression: bool = False) -> Commit:
    return Commit(
        id=uuid4(),
        repository_id=uuid4(),
        sha="c" * 40,
        message="fix bug in parser",
        author_email="dev@example.com",
        committed_at=datetime.now(UTC),
        is_regression=is_regression,
        metadata={"parent_sha": "p" * 40, "changed_files": ["b.py"]},
    )
