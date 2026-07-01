"""PyG-compatible dataset for GNN training."""

from __future__ import annotations

from dataclasses import dataclass

import torch
from torch.utils.data import Dataset

from code_impact.domain.services import DiffAnalysisResult
from code_impact.ml.features.graph_converter import graph_to_tensors, labels_to_node_targets
from code_impact.ml.training.types import TrainingSample


@dataclass(frozen=True, slots=True)
class GraphDataItem:
    x: torch.Tensor
    edge_index: torch.Tensor
    batch: torch.Tensor
    historical: torch.Tensor | None
    risk_target: float
    regression_target: float
    node_targets: torch.Tensor
    file_mask: torch.Tensor
    sample_id: str


class CodeImpactDataset(Dataset):
    """In-memory dataset of graph training samples."""

    def __init__(self, samples: list[TrainingSample], device: str = "cpu") -> None:
        self._items: list[GraphDataItem] = []
        for sample in samples:
            diff_result = DiffAnalysisResult(
                changed_files=sample.changed_files,
                added_lines=max(len(sample.diff.splitlines()), 1),
                deleted_lines=0,
                modified_functions=[],
                renamed_files={},
                complexity_delta=0.0,
                deleted_code_ratio=0.0,
                raw_diff=sample.diff,
            )
            bundle = graph_to_tensors(sample.graph_snapshot, diff_result, device=device)
            node_targets = labels_to_node_targets(bundle, sample.labels.affected_files)
            file_mask = torch.zeros(len(bundle.node_ids), dtype=torch.float32)
            for idx in bundle.file_node_indices:
                file_mask[idx] = 1.0

            hist = None
            if sample.historical_embedding:
                hist = torch.tensor(sample.historical_embedding, dtype=torch.float32)

            self._items.append(
                GraphDataItem(
                    x=bundle.x,
                    edge_index=bundle.edge_index,
                    batch=bundle.batch,
                    historical=hist,
                    risk_target=sample.labels.risk_score,
                    regression_target=sample.labels.is_regression,
                    node_targets=node_targets,
                    file_mask=file_mask,
                    sample_id=sample.next_commit_sha,
                )
            )

    def __len__(self) -> int:
        return len(self._items)

    def __getitem__(self, index: int) -> GraphDataItem:
        return self._items[index]


def collate_graph_items(items: list[GraphDataItem]) -> dict[str, torch.Tensor]:
    """Batch graphs by concatenating nodes (batch size is typically small)."""
    if len(items) == 1:
        item = items[0]
        hist = item.historical.unsqueeze(0) if item.historical is not None else None
        return {
            "x": item.x,
            "edge_index": item.edge_index,
            "batch": item.batch,
            "historical": hist,
            "risk_target": torch.tensor([item.risk_target], dtype=torch.float32),
            "regression_target": torch.tensor([item.regression_target], dtype=torch.float32),
            "node_targets": item.node_targets,
            "file_mask": item.file_mask,
        }

    xs: list[torch.Tensor] = []
    edge_indices: list[torch.Tensor] = []
    batches: list[torch.Tensor] = []
    node_targets: list[torch.Tensor] = []
    file_masks: list[torch.Tensor] = []
    risk_targets: list[float] = []
    regression_targets: list[float] = []
    historical: list[torch.Tensor] = []
    node_offset = 0

    for batch_idx, item in enumerate(items):
        xs.append(item.x)
        edge_indices.append(item.edge_index + node_offset)
        batches.append(item.batch + batch_idx)
        node_targets.append(item.node_targets)
        file_masks.append(item.file_mask)
        risk_targets.append(item.risk_target)
        regression_targets.append(item.regression_target)
        if item.historical is not None:
            historical.append(item.historical)
        node_offset += item.x.size(0)

    hist_tensor = torch.stack(historical) if historical else None
    return {
        "x": torch.cat(xs, dim=0),
        "edge_index": torch.cat(edge_indices, dim=1),
        "batch": torch.cat(batches, dim=0),
        "historical": hist_tensor,
        "risk_target": torch.tensor(risk_targets, dtype=torch.float32),
        "regression_target": torch.tensor(regression_targets, dtype=torch.float32),
        "node_targets": torch.cat(node_targets, dim=0),
        "file_mask": torch.cat(file_masks, dim=0),
    }
