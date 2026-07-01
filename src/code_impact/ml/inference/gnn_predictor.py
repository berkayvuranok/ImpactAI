"""Production GNN inference service."""

from __future__ import annotations

import asyncio
from pathlib import Path

import torch

from code_impact.domain.entities import GraphSnapshot
from code_impact.domain.services import DiffAnalysisResult, GNNPredictionResult, IGNNPredictor
from code_impact.domain.value_objects.risk import (
    AffectedFilePrediction,
    ConfidenceScore,
    RegressionProbability,
    RiskScore,
)
from code_impact.ml.features.graph_converter import graph_to_tensors
from code_impact.ml.model_registry import load_artifact


class GNNPredictor(IGNNPredictor):
    """Loads CodeImpactGNN checkpoint and runs forward pass."""

    def __init__(self, model_path: str, device: str = "cpu") -> None:
        self._model_path = model_path
        self._device = device
        self._model = None
        self._config = None
        self._load()

    def _load(self) -> None:
        path = Path(self._model_path)
        if not path.exists():
            return
        model, config, _metrics = load_artifact(path)
        self._model = model
        self._config = config
        self._model.to(self._device)
        self._model.eval()

    @property
    def is_loaded(self) -> bool:
        return self._model is not None

    async def predict(
        self,
        graph_snapshot: GraphSnapshot,
        diff_result: DiffAnalysisResult,
        historical_embedding: list[float] | None = None,
    ) -> GNNPredictionResult:
        if self._model is None:
            msg = f"GNN model not found at {self._model_path}"
            raise FileNotFoundError(msg)
        return await asyncio.to_thread(
            self._predict_sync, graph_snapshot, diff_result, historical_embedding
        )

    def _predict_sync(
        self,
        graph_snapshot: GraphSnapshot,
        diff_result: DiffAnalysisResult,
        historical_embedding: list[float] | None,
    ) -> GNNPredictionResult:
        assert self._model is not None
        bundle = graph_to_tensors(graph_snapshot, diff_result, device=self._device)
        hist = None
        if historical_embedding:
            hist = torch.tensor(historical_embedding, dtype=torch.float32, device=self._device)

        with torch.no_grad():
            out = self._model(
                bundle.x,
                bundle.edge_index,
                bundle.batch,
                hist.unsqueeze(0) if hist is not None and hist.dim() == 1 else hist,
            )

        risk = float(out["risk_score"][0].cpu())
        reg_prob = float(torch.sigmoid(out["regression_logit"][0]).cpu())
        confidence = float(out["confidence"][0].cpu())
        node_logits = out["node_logits"].cpu()
        node_probs = torch.sigmoid(node_logits).tolist()

        affected = self._rank_affected_files(bundle, node_probs, node_logits.tolist())
        node_importance = {
            bundle.node_ids[idx]: float(node_probs[idx]) for idx in range(len(bundle.node_ids))
        }

        return GNNPredictionResult(
            risk_score=RiskScore(min(max(risk, 0.0), 100.0)),
            regression_probability=RegressionProbability(min(max(reg_prob, 0.0), 1.0)),
            confidence_score=ConfidenceScore(min(max(confidence, 0.0), 1.0)),
            affected_files=affected,
            node_importance=node_importance,
            edge_importance=[],
        )

    @staticmethod
    def _rank_affected_files(
        bundle,
        node_probs: list[float],
        raw_logits: list[float],
        top_k: int = 10,
    ) -> list[AffectedFilePrediction]:
        ranked: list[tuple[str, float, float, int]] = []
        for rank_idx, node_idx in enumerate(bundle.file_node_indices):
            if node_idx >= len(node_probs):
                continue
            path = bundle.file_paths[rank_idx] if rank_idx < len(bundle.file_paths) else ""
            if not path:
                continue
            ranked.append((path, node_probs[node_idx], abs(raw_logits[node_idx]), rank_idx))

        ranked.sort(key=lambda item: item[1], reverse=True)
        return [
            AffectedFilePrediction(
                file_path=path,
                break_probability=min(max(prob, 0.0), 1.0),
                node_importance=min(max(importance, 0.0), 1.0),
                rank=rank + 1,
            )
            for rank, (path, prob, importance, _idx) in enumerate(ranked[:top_k])
        ]
