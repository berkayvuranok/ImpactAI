"""XAI report types — SHAP feature attributions and GNN attention."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class FeatureAttribution:
    feature: str
    value: float
    shap_value: float
    label: str = ""


@dataclass(frozen=True, slots=True)
class NodeAttention:
    node_id: str
    name: str
    file_path: str | None
    attention_score: float
    rank: int


@dataclass(frozen=True, slots=True)
class EdgeAttention:
    source_id: str
    target_id: str
    attention_score: float


@dataclass(frozen=True, slots=True)
class XAIReport:
    shap_base_value: float
    shap_output_value: float
    feature_attributions: list[FeatureAttribution]
    node_attentions: list[NodeAttention]
    edge_attentions: list[EdgeAttention] = field(default_factory=list)
    method: str = "linear_shap+node_logits"
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "shap_base_value": self.shap_base_value,
            "shap_output_value": self.shap_output_value,
            "feature_attributions": [
                {
                    "feature": f.feature,
                    "label": f.label or f.feature,
                    "value": f.value,
                    "shap_value": f.shap_value,
                }
                for f in self.feature_attributions
            ],
            "node_attentions": [
                {
                    "node_id": n.node_id,
                    "name": n.name,
                    "file_path": n.file_path,
                    "attention_score": n.attention_score,
                    "rank": n.rank,
                }
                for n in self.node_attentions
            ],
            "edge_attentions": [
                {
                    "source_id": e.source_id,
                    "target_id": e.target_id,
                    "attention_score": e.attention_score,
                }
                for e in self.edge_attentions
            ],
            "method": self.method,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict) -> XAIReport:
        return cls(
            shap_base_value=float(data.get("shap_base_value", 0.0)),
            shap_output_value=float(data.get("shap_output_value", 0.0)),
            feature_attributions=[
                FeatureAttribution(
                    feature=f["feature"],
                    value=float(f["value"]),
                    shap_value=float(f["shap_value"]),
                    label=f.get("label", f["feature"]),
                )
                for f in data.get("feature_attributions", [])
            ],
            node_attentions=[
                NodeAttention(
                    node_id=n["node_id"],
                    name=n["name"],
                    file_path=n.get("file_path"),
                    attention_score=float(n["attention_score"]),
                    rank=int(n["rank"]),
                )
                for n in data.get("node_attentions", [])
            ],
            edge_attentions=[
                EdgeAttention(
                    source_id=e["source_id"],
                    target_id=e["target_id"],
                    attention_score=float(e["attention_score"]),
                )
                for e in data.get("edge_attentions", [])
            ],
            method=str(data.get("method", "unknown")),
            metadata=dict(data.get("metadata", {})),
        )
