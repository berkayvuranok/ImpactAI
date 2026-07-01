"""GNN node/edge attention extraction from prediction outputs."""

from __future__ import annotations

from code_impact.domain.entities import GraphSnapshot
from code_impact.domain.services import GNNPredictionResult
from code_impact.ml.xai.types import EdgeAttention, NodeAttention


def extract_node_attention(
    gnn_result: GNNPredictionResult,
    graph: GraphSnapshot | None,
    *,
    top_k: int = 15,
) -> list[NodeAttention]:
    node_lookup = {}
    if graph:
        node_lookup = {n.node_id: n for n in graph.nodes}

    ranked = sorted(
        gnn_result.node_importance.items(),
        key=lambda item: item[1],
        reverse=True,
    )[:top_k]

    attentions: list[NodeAttention] = []
    for rank, (node_id, score) in enumerate(ranked, start=1):
        node = node_lookup.get(node_id)
        attentions.append(
            NodeAttention(
                node_id=node_id,
                name=node.name if node else node_id,
                file_path=node.file_path if node else None,
                attention_score=min(max(float(score), 0.0), 1.0),
                rank=rank,
            )
        )
    return attentions


def extract_edge_attention(
    gnn_result: GNNPredictionResult,
    *,
    top_k: int = 10,
) -> list[EdgeAttention]:
    edges = gnn_result.edge_importance or []
    ranked = sorted(edges, key=lambda e: e[2], reverse=True)[:top_k]
    return [
        EdgeAttention(
            source_id=src,
            target_id=tgt,
            attention_score=min(max(float(score), 0.0), 1.0),
        )
        for src, tgt, score in ranked
    ]
