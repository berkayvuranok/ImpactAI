"""Unit tests for subgraph extraction."""

from uuid import uuid4

from code_impact.domain.entities import GraphEdge, GraphNode, GraphSnapshot
from code_impact.domain.value_objects.enums import EdgeType, NodeType
from code_impact.infrastructure.graph.subgraph_extractor import extract_subgraph, seeds_for_files


def _snapshot() -> GraphSnapshot:
    sid = uuid4()
    nodes = [
        GraphNode(uuid4(), sid, "file:a.py", NodeType.FILE, "a.py", "a.py"),
        GraphNode(uuid4(), sid, "file:b.py", NodeType.FILE, "b.py", "b.py"),
        GraphNode(uuid4(), sid, "file:c.py", NodeType.FILE, "c.py", "c.py"),
    ]
    edges = [
        GraphEdge(uuid4(), sid, "file:a.py", "file:b.py", EdgeType.IMPORT),
        GraphEdge(uuid4(), sid, "file:b.py", "file:c.py", EdgeType.IMPORT),
    ]
    return GraphSnapshot(
        id=sid,
        repository_id=uuid4(),
        commit_sha="abc",
        node_count=3,
        edge_count=2,
        storage_path="",
        nodes=nodes,
        edges=edges,
    )


def test_extract_subgraph_bfs():
    snapshot = _snapshot()
    sub_nodes, sub_edges = extract_subgraph(snapshot, ["file:a.py"], max_depth=2)
    node_ids = {n.node_id for n in sub_nodes}
    assert "file:a.py" in node_ids
    assert "file:b.py" in node_ids
    assert "file:c.py" in node_ids
    assert len(sub_edges) == 2


def test_seeds_for_files():
    snapshot = _snapshot()
    seeds = seeds_for_files(snapshot, ["a.py"])
    assert "file:a.py" in seeds
