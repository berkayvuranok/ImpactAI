"""Heuristic GNN predictor for tests and environments without a trained checkpoint."""

from __future__ import annotations

from code_impact.domain.entities import GraphSnapshot
from code_impact.domain.services import DiffAnalysisResult, GNNPredictionResult, IGNNPredictor
from code_impact.domain.value_objects.enums import NodeType
from code_impact.domain.value_objects.risk import (
    AffectedFilePrediction,
    ConfidenceScore,
    RegressionProbability,
    RiskScore,
)
from code_impact.ml.features.node_feature_builder import NodeFeatureBuilder


class MockGNNPredictor(IGNNPredictor):
    """Deterministic heuristic predictor — not an LLM."""

    async def predict(
        self,
        graph_snapshot: GraphSnapshot,
        diff_result: DiffAnalysisResult,
        historical_embedding: list[float] | None = None,
    ) -> GNNPredictionResult:
        base_risk = min(
            15.0
            + diff_result.added_lines * 0.04
            + diff_result.deleted_lines * 0.06
            + abs(diff_result.complexity_delta) * 1.5
            + len(diff_result.changed_files) * 2.5,
            90.0,
        )
        if historical_embedding:
            hist_signal = sum(abs(v) for v in historical_embedding[:32]) / max(len(historical_embedding[:32]), 1)
            base_risk = min(base_risk + hist_signal * 5.0, 95.0)

        reg_prob = min(base_risk / 100.0 + diff_result.deleted_code_ratio * 0.2, 0.95)
        confidence = 0.55 if graph_snapshot.node_count > 0 else 0.35

        builder = NodeFeatureBuilder()
        _features, node_ids, file_indices = builder.build(graph_snapshot, diff_result)
        node_importance: dict[str, float] = {}
        for idx, node_id in enumerate(node_ids):
            node = graph_snapshot.nodes[idx]
            score = 0.1
            if node.file_path in diff_result.changed_files:
                score += 0.5
            if node.node_type == NodeType.FILE:
                score += 0.2
            node_importance[node_id] = min(score, 1.0)

        affected_paths = list(diff_result.changed_files)
        for node_idx in file_indices:
            node = graph_snapshot.nodes[node_idx]
            path = node.file_path or node.name
            if path and path not in affected_paths:
                affected_paths.append(path)

        affected = [
            AffectedFilePrediction(
                file_path=path,
                break_probability=min(reg_prob + 0.05 * i, 0.99),
                node_importance=node_importance.get(f"file:{path}", 0.3),
                rank=i + 1,
            )
            for i, path in enumerate(affected_paths[:10])
        ]

        return GNNPredictionResult(
            risk_score=RiskScore(base_risk),
            regression_probability=RegressionProbability(reg_prob),
            confidence_score=ConfidenceScore(confidence),
            affected_files=affected,
            node_importance=node_importance,
            edge_importance=[],
        )
