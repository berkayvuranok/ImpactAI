"""Tests for node feature builder."""

from support.ml_fixtures import sample_diff, sample_graph

from code_impact.ml.features.node_feature_builder import NODE_FEATURE_DIM, NodeFeatureBuilder


def test_node_feature_shape():
    builder = NodeFeatureBuilder()
    features, node_ids, file_indices = builder.build(sample_graph(), sample_diff())
    assert features.shape == (4, NODE_FEATURE_DIM)
    assert len(node_ids) == 4
    assert file_indices == [0, 1, 2]


def test_changed_file_flag():
    builder = NodeFeatureBuilder()
    features, _, _ = builder.build(sample_graph(), sample_diff())
    # First file node is a.py (changed)
    assert features[0][5] == 1.0
