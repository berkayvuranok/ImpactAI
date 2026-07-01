"""XAI service — combines SHAP and GNN attention into a unified report."""

from __future__ import annotations

from code_impact.domain.entities import GraphSnapshot
from code_impact.domain.services import DiffAnalysisResult, GNNPredictionResult
from code_impact.ml.risk.feature_extractor import DiffRiskFeatures, extract_risk_features
from code_impact.ml.xai.attention_extractor import extract_edge_attention, extract_node_attention
from code_impact.ml.xai.shap_explainer import explain_classical_features, explain_classical_with_shap_library
from code_impact.ml.xai.types import XAIReport


class XAIService:
    def __init__(self, *, use_shap_library: bool = False) -> None:
        self._use_shap_library = use_shap_library

    def explain(
        self,
        diff_result: DiffAnalysisResult,
        gnn_result: GNNPredictionResult,
        graph_snapshot: GraphSnapshot | None = None,
        features: DiffRiskFeatures | None = None,
    ) -> XAIReport:
        feat = features or extract_risk_features(diff_result)

        method = "linear_exact+node_logits"
        if self._use_shap_library:
            base, out, attributions, shap_method = explain_classical_with_shap_library(feat)
            method = f"{shap_method}+node_logits"
        else:
            base, out, attributions = explain_classical_features(feat)

        node_attentions = extract_node_attention(gnn_result, graph_snapshot)
        edge_attentions = extract_edge_attention(gnn_result)

        return XAIReport(
            shap_base_value=base,
            shap_output_value=out,
            feature_attributions=attributions,
            node_attentions=node_attentions,
            edge_attentions=edge_attentions,
            method=method,
            metadata={
                "gnn_risk": gnn_result.risk_score.value,
                "gnn_confidence": gnn_result.confidence_score.value,
                "node_count": len(gnn_result.node_importance),
                "edge_count": len(edge_attentions),
            },
        )
