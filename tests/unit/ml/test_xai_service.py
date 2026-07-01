"""Unit tests for XAI SHAP and attention extractors."""

from uuid import uuid4

import pytest

from code_impact.domain.entities import GraphNode, GraphSnapshot
from code_impact.domain.services import DiffAnalysisResult, GNNPredictionResult
from code_impact.domain.value_objects.enums import NodeType
from code_impact.domain.value_objects.risk import (
    AffectedFilePrediction,
    ConfidenceScore,
    RegressionProbability,
    RiskScore,
)
from code_impact.ml.risk.feature_extractor import extract_risk_features
from code_impact.ml.xai import XAIService, explain_classical_features
from code_impact.ml.xai.types import XAIReport


def _diff_result() -> DiffAnalysisResult:
    return DiffAnalysisResult(
        changed_files=["src/a.py"],
        added_lines=40,
        deleted_lines=10,
        modified_functions=["foo"],
        renamed_files={},
        complexity_delta=2.5,
        deleted_code_ratio=0.1,
        raw_diff="",
    )


def _gnn_result() -> GNNPredictionResult:
    return GNNPredictionResult(
        risk_score=RiskScore(55.0),
        regression_probability=RegressionProbability(0.4),
        confidence_score=ConfidenceScore(0.7),
        affected_files=[
            AffectedFilePrediction(
                file_path="src/a.py",
                break_probability=0.6,
                node_importance=0.8,
                rank=1,
            )
        ],
        node_importance={"node-1": 0.9, "node-2": 0.3},
        edge_importance=[("node-1", "node-2", 0.75)],
    )


def test_linear_shap_sums_to_output():
    features = extract_risk_features(_diff_result())
    base, out, attrs = explain_classical_features(features)
    total = base + sum(a.shap_value for a in attrs)
    assert abs(total - out) < 1e-6
    assert len(attrs) == 10


def test_xai_service_builds_report():
    diff = _diff_result()
    gnn = _gnn_result()
    graph = GraphSnapshot(
        id=uuid4(),
        repository_id=uuid4(),
        commit_sha="abc1234",
        node_count=2,
        edge_count=1,
        storage_path="",
        nodes=[
            GraphNode(
                id=uuid4(),
                snapshot_id=uuid4(),
                node_id="node-1",
                node_type=NodeType.FILE,
                name="a.py",
                file_path="src/a.py",
            ),
            GraphNode(
                id=uuid4(),
                snapshot_id=uuid4(),
                node_id="node-2",
                node_type=NodeType.FUNCTION,
                name="foo",
                file_path="src/a.py",
            ),
        ],
    )
    report = XAIService().explain(diff, gnn, graph_snapshot=graph)
    assert isinstance(report, XAIReport)
    assert report.feature_attributions
    assert report.node_attentions[0].name == "a.py"
    assert report.edge_attentions[0].attention_score == pytest.approx(0.75)


def test_xai_report_roundtrip_dict():
    report = XAIService().explain(_diff_result(), _gnn_result())
    restored = XAIReport.from_dict(report.to_dict())
    assert restored.method == report.method
    assert len(restored.feature_attributions) == len(report.feature_attributions)
