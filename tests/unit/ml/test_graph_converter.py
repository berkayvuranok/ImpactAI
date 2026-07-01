"""Tests for graph tensor conversion."""

import pytest

torch = pytest.importorskip("torch")

from support.ml_fixtures import sample_diff, sample_graph

from code_impact.ml.features.graph_converter import graph_to_tensors, labels_to_node_targets


def test_graph_to_tensors():
    bundle = graph_to_tensors(sample_graph(), sample_diff(), device="cpu")
    assert bundle.x.shape[0] == 4
    assert bundle.edge_index.shape[0] == 2
    assert len(bundle.file_paths) == 3


def test_labels_to_node_targets():
    bundle = graph_to_tensors(sample_graph(), sample_diff(), device="cpu")
    targets = labels_to_node_targets(bundle, ["b.py"])
    assert targets.shape[0] == 4
    assert targets.sum().item() >= 1.0
