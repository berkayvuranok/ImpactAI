"""Tests for CodeImpactGNN forward pass."""

import pytest

torch = pytest.importorskip("torch")

from code_impact.ml.features.graph_converter import graph_to_tensors
from code_impact.ml.models.code_impact_gnn import CodeImpactGNN, GNNConfig
from support.ml_fixtures import sample_diff, sample_graph


def test_code_impact_gnn_forward():
    bundle = graph_to_tensors(sample_graph(), sample_diff(), device="cpu")
    model = CodeImpactGNN(GNNConfig(in_channels=bundle.x.shape[1], historical_dim=384))
    hist = torch.zeros(1, 384)
    out = model(bundle.x, bundle.edge_index, bundle.batch, hist)
    assert out["risk_score"].shape == (1,)
    assert out["node_logits"].shape[0] == bundle.x.shape[0]
