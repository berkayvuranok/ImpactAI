"""GNN training loop."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import torch
import torch.nn.functional as F
from torch.utils.data import DataLoader

from code_impact.ml.evaluation.metrics import compute_metrics
from code_impact.ml.models.code_impact_gnn import CodeImpactGNN, GNNConfig
from code_impact.ml.model_registry import ModelArtifact, save_artifact
from code_impact.ml.training.dataset import CodeImpactDataset, collate_graph_items


@dataclass(frozen=True, slots=True)
class TrainConfig:
    epochs: int = 10
    learning_rate: float = 1e-3
    batch_size: int = 8
    device: str = "cpu"
    risk_weight: float = 1.0
    regression_weight: float = 1.0
    node_weight: float = 0.5


@dataclass(frozen=True, slots=True)
class TrainResult:
    artifact_path: str
    metrics: dict[str, float]
    epochs_trained: int


class GNNTrainer:
    def __init__(
        self,
        model: CodeImpactGNN | None = None,
        config: GNNConfig | None = None,
        train_config: TrainConfig | None = None,
    ) -> None:
        self._gnn_config = config or GNNConfig()
        self._train_config = train_config or TrainConfig()
        self._device = torch.device(self._train_config.device)
        self._model = model or CodeImpactGNN(self._gnn_config)
        self._model.to(self._device)

    def train(
        self,
        train_samples: list,
        val_samples: list | None = None,
        output_path: str | Path = "models/gnn/latest.pt",
    ) -> TrainResult:
        train_ds = CodeImpactDataset(train_samples, device=str(self._device))
        train_loader = DataLoader(
            train_ds,
            batch_size=min(self._train_config.batch_size, max(len(train_ds), 1)),
            shuffle=True,
            collate_fn=collate_graph_items,
        )

        val_loader = None
        if val_samples:
            val_ds = CodeImpactDataset(val_samples, device=str(self._device))
            val_loader = DataLoader(
                val_ds,
                batch_size=min(self._train_config.batch_size, max(len(val_ds), 1)),
                shuffle=False,
                collate_fn=collate_graph_items,
            )

        optimizer = torch.optim.Adam(self._model.parameters(), lr=self._train_config.learning_rate)
        self._model.train()

        for _epoch in range(self._train_config.epochs):
            for batch in train_loader:
                optimizer.zero_grad()
                loss = self._compute_loss(batch)
                loss.backward()
                optimizer.step()

        metrics = self.evaluate(val_loader or train_loader)
        artifact = ModelArtifact(
            model_state=self._model.state_dict(),
            gnn_config=self._gnn_config,
            metrics=metrics,
        )
        path = save_artifact(artifact, output_path)
        return TrainResult(artifact_path=str(path), metrics=metrics, epochs_trained=self._train_config.epochs)

    def evaluate(self, loader: DataLoader) -> dict[str, float]:
        self._model.eval()
        preds: list[dict[str, float]] = []
        labels: list[dict[str, float | list[str]]] = []

        with torch.no_grad():
            for batch in loader:
                batch = {k: v.to(self._device) if isinstance(v, torch.Tensor) else v for k, v in batch.items()}
                out = self._model(
                    batch["x"],
                    batch["edge_index"],
                    batch["batch"],
                    batch.get("historical"),
                )
                risk = out["risk_score"].cpu().tolist()
                reg = torch.sigmoid(out["regression_logit"]).cpu().tolist()
                for i, r in enumerate(risk):
                    preds.append({"risk_score": r, "regression_probability": reg[i]})
                    labels.append(
                        {
                            "risk_score": float(batch["risk_target"][i]),
                            "is_regression": float(batch["regression_target"][i]),
                            "affected_files": [],
                        }
                    )

        self._model.train()
        return compute_metrics(preds, labels)

    def _compute_loss(self, batch: dict[str, torch.Tensor]) -> torch.Tensor:
        batch = {k: v.to(self._device) if isinstance(v, torch.Tensor) else v for k, v in batch.items()}
        out = self._model(
            batch["x"],
            batch["edge_index"],
            batch["batch"],
            batch.get("historical"),
        )
        tc = self._train_config
        risk_loss = F.mse_loss(out["risk_score"], batch["risk_target"]) * tc.risk_weight
        reg_loss = F.binary_cross_entropy_with_logits(
            out["regression_logit"], batch["regression_target"]
        ) * tc.regression_weight
        node_logits = out["node_logits"]
        node_loss = F.binary_cross_entropy_with_logits(
            node_logits, batch["node_targets"], reduction="none"
        )
        mask = batch["file_mask"]
        if mask.sum() > 0:
            node_loss = (node_loss * mask).sum() / mask.sum()
        else:
            node_loss = node_loss.mean()
        return risk_loss + reg_loss + node_loss * tc.node_weight
