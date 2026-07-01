"""Explainability (XAI) layer."""

from code_impact.ml.xai.attention_extractor import extract_edge_attention, extract_node_attention
from code_impact.ml.xai.shap_explainer import explain_classical_features, explain_classical_with_shap_library
from code_impact.ml.xai.types import EdgeAttention, FeatureAttribution, NodeAttention, XAIReport
from code_impact.ml.xai.xai_service import XAIService

__all__ = [
    "EdgeAttention",
    "FeatureAttribution",
    "NodeAttention",
    "XAIReport",
    "XAIService",
    "explain_classical_features",
    "explain_classical_with_shap_library",
    "extract_edge_attention",
    "extract_node_attention",
]
