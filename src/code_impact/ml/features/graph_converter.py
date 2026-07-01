"""Convert domain graph snapshots to PyG tensors."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from code_impact.domain.entities import GraphSnapshot
from code_impact.domain.services import DiffAnalysisResult
from code_impact.ml.features.node_feature_builder import NODE_FEATURE_DIM, NodeFeatureBuilder


@dataclass(frozen=True, slots=True)
class GraphTensorBundle:
    x: object
    edge_index: object
    batch: object
    node_ids: list[str]
    file_node_indices: list[int]
    file_paths: list[str]
    node_id_to_index: dict[str, int]


def graph_to_tensors(
    snapshot: GraphSnapshot,
    diff_result: DiffAnalysisResult | None = None,
    device: str = "cpu",
    bug_counts: dict[str, int] | None = None,
) -> GraphTensorBundle:
    import torch

    builder = NodeFeatureBuilder()
    features, node_ids, file_indices = builder.build(snapshot, diff_result, bug_counts)

    index = {nid: i for i, nid in enumerate(node_ids)}
    src: list[int] = []
    dst: list[int] = []
    for edge in snapshot.edges:
        if edge.source_id in index and edge.target_id in index:
            src.append(index[edge.source_id])
            dst.append(index[edge.target_id])

    if src:
        edge_index = torch.tensor([src, dst], dtype=torch.long)
    else:
        edge_index = torch.zeros((2, 0), dtype=torch.long)

    if len(node_ids) == 0:
        x = torch.zeros((0, NODE_FEATURE_DIM), dtype=torch.float32)
    else:
        x = torch.from_numpy(features)

    batch = torch.zeros(len(node_ids), dtype=torch.long)
    file_paths = [
        snapshot.nodes[i].file_path or snapshot.nodes[i].name
        for i in file_indices
        if i < len(snapshot.nodes)
    ]

    return GraphTensorBundle(
        x=x.to(device),
        edge_index=edge_index.to(device),
        batch=batch.to(device),
        node_ids=node_ids,
        file_node_indices=file_indices,
        file_paths=file_paths,
        node_id_to_index=index,
    )


def labels_to_node_targets(
    bundle: GraphTensorBundle,
    affected_files: list[str],
) -> object:
    """Multi-label targets aligned with all nodes (1 = likely affected file node)."""
    import torch

    affected = set(affected_files)
    targets = []
    for idx, node_id in enumerate(bundle.node_ids):
        if idx not in bundle.file_node_indices:
            targets.append(0.0)
            continue
        file_idx = bundle.file_node_indices.index(idx)
        path = bundle.file_paths[file_idx] if file_idx < len(bundle.file_paths) else ""
        targets.append(1.0 if path in affected else 0.0)
    return torch.tensor(targets, dtype=torch.float32)
