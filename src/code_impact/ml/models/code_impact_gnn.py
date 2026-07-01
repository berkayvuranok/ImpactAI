"""CodeImpactGNN — GraphSAGE encoder with risk and affected-file heads."""

from __future__ import annotations

from dataclasses import dataclass

import torch
import torch.nn.functional as F
from torch import Tensor, nn
from torch_geometric.nn import SAGEConv, global_mean_pool


@dataclass(frozen=True, slots=True)
class GNNConfig:
    in_channels: int = 32
    hidden_channels: int = 256
    out_channels: int = 128
    num_layers: int = 3
    dropout: float = 0.2
    historical_dim: int = 384


class CodeImpactGNN(nn.Module):
    """GraphSAGE GNN for code impact prediction (not LLM)."""

    def __init__(self, config: GNNConfig | None = None) -> None:
        super().__init__()
        self.config = config or GNNConfig()
        cfg = self.config

        dims = [cfg.in_channels] + [cfg.hidden_channels] * (cfg.num_layers - 1) + [cfg.out_channels]
        self.convs = nn.ModuleList(
            [SAGEConv(dims[i], dims[i + 1]) for i in range(cfg.num_layers)]
        )
        self.batch_norms = nn.ModuleList([nn.BatchNorm1d(d) for d in dims[1:]])

        graph_input_dim = cfg.out_channels + cfg.historical_dim
        self.risk_head = nn.Sequential(
            nn.Linear(graph_input_dim, 64),
            nn.ReLU(),
            nn.Dropout(cfg.dropout),
            nn.Linear(64, 2),
        )
        self.confidence_head = nn.Sequential(
            nn.Linear(graph_input_dim, 32),
            nn.ReLU(),
            nn.Linear(32, 1),
        )
        self.node_head = nn.Sequential(
            nn.Linear(cfg.out_channels, 32),
            nn.ReLU(),
            nn.Linear(32, 1),
        )

    def encode(self, x: Tensor, edge_index: Tensor) -> Tensor:
        h = x
        for conv, bn in zip(self.convs, self.batch_norms, strict=True):
            h = conv(h, edge_index)
            h = bn(h)
            h = F.relu(h)
            h = F.dropout(h, p=self.config.dropout, training=self.training)
        return h

    def forward(
        self,
        x: Tensor,
        edge_index: Tensor,
        batch: Tensor,
        historical_embedding: Tensor | None = None,
    ) -> dict[str, Tensor]:
        node_embeddings = self.encode(x, edge_index)
        node_logits = self.node_head(node_embeddings).squeeze(-1)

        graph_embedding = global_mean_pool(node_embeddings, batch)
        if historical_embedding is None:
            hist = torch.zeros(
                graph_embedding.size(0),
                self.config.historical_dim,
                device=graph_embedding.device,
                dtype=graph_embedding.dtype,
            )
        else:
            hist = historical_embedding
            if hist.dim() == 1:
                hist = hist.unsqueeze(0)

        fused = torch.cat([graph_embedding, hist], dim=-1)
        risk_out = self.risk_head(fused)
        risk_score = torch.sigmoid(risk_out[:, 0]) * 100.0
        regression_logit = risk_out[:, 1]
        confidence = torch.sigmoid(self.confidence_head(fused)).squeeze(-1)

        return {
            "risk_score": risk_score,
            "regression_logit": regression_logit,
            "node_logits": node_logits,
            "confidence": confidence,
            "node_embeddings": node_embeddings,
            "graph_embedding": graph_embedding,
        }
