"""Extract subgraphs around seed nodes via BFS."""

from __future__ import annotations

from collections import deque

from code_impact.domain.entities import GraphEdge, GraphNode, GraphSnapshot


def extract_subgraph(
    snapshot: GraphSnapshot,
    seed_node_ids: list[str],
    *,
    max_depth: int = 2,
    max_nodes: int = 500,
) -> tuple[list[GraphNode], list[GraphEdge]]:
    adjacency: dict[str, list[tuple[str, GraphEdge]]] = {}
    for edge in snapshot.edges:
        adjacency.setdefault(edge.source_id, []).append((edge.target_id, edge))
        adjacency.setdefault(edge.target_id, []).append((edge.source_id, edge))

    node_map = {n.node_id: n for n in snapshot.nodes}
    visited: set[str] = set()
    collected_edges: dict[tuple[str, str, str], GraphEdge] = {}
    queue: deque[tuple[str, int]] = deque()

    for seed in seed_node_ids:
        if seed in node_map:
            queue.append((seed, 0))
            visited.add(seed)

    while queue and len(visited) < max_nodes:
        node_id, depth = queue.popleft()
        if depth >= max_depth:
            continue
        for neighbor, edge in adjacency.get(node_id, []):
            key = (edge.source_id, edge.target_id, edge.edge_type.value)
            collected_edges[key] = edge
            if neighbor not in visited and len(visited) < max_nodes:
                visited.add(neighbor)
                queue.append((neighbor, depth + 1))

    sub_nodes = [node_map[nid] for nid in visited if nid in node_map]
    sub_edges = list(collected_edges.values())
    return sub_nodes, sub_edges


def seeds_for_files(snapshot: GraphSnapshot, file_paths: list[str]) -> list[str]:
    from code_impact.infrastructure.graph.node_ids import file_id

    seeds = [file_id(p) for p in file_paths]
    for node in snapshot.nodes:
        if node.file_path in file_paths:
            seeds.append(node.node_id)
    return list(dict.fromkeys(seeds))
