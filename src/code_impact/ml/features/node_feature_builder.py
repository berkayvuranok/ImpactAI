"""Per-node feature vectors for GNN input."""

from __future__ import annotations

import math
from collections import defaultdict

import numpy as np

from code_impact.domain.entities import GraphNode, GraphSnapshot
from code_impact.domain.services import DiffAnalysisResult
from code_impact.domain.value_objects.enums import NodeType

NODE_TYPE_ORDER = [
    NodeType.FILE,
    NodeType.CLASS,
    NodeType.FUNCTION,
    NodeType.MODULE,
    NodeType.SERVICE,
]
NODE_TYPE_COUNT = len(NODE_TYPE_ORDER)
# 5 one-hot + 27 scalar features
NODE_FEATURE_DIM = 32


class NodeFeatureBuilder:
    """Build fixed-size node feature vectors from graph + diff context."""

    def __init__(self) -> None:
        self._type_index = {t: i for i, t in enumerate(NODE_TYPE_ORDER)}

    def build(
        self,
        snapshot: GraphSnapshot,
        diff_result: DiffAnalysisResult | None = None,
        bug_counts: dict[str, int] | None = None,
    ) -> tuple[np.ndarray, list[str], list[int]]:
        """Return (feature_matrix, node_ids, file_node_indices)."""
        nodes = snapshot.nodes
        if not nodes:
            return np.zeros((0, NODE_FEATURE_DIM), dtype=np.float32), [], []

        changed_files = set(diff_result.changed_files if diff_result else [])
        file_line_stats = self._file_line_stats(diff_result)
        bug_counts = bug_counts or {}

        in_degree, out_degree = self._degrees(snapshot)
        pagerank = self._pagerank(snapshot, nodes)
        max_degree = max(max(in_degree.values(), default=1), max(out_degree.values(), default=1), 1)

        node_ids: list[str] = []
        file_node_indices: list[int] = []
        rows: list[list[float]] = []

        for idx, node in enumerate(nodes):
            node_ids.append(node.node_id)
            if node.node_type == NodeType.FILE:
                file_node_indices.append(idx)

            props = node.properties or {}
            file_path = node.file_path or node.name
            is_changed = float(file_path in changed_files or node.name in changed_files)
            added, deleted = file_line_stats.get(file_path, (0, 0))
            complexity = float(props.get("complexity", props.get("cyclomatic_complexity", 0.0)))
            loc = float(props.get("loc", props.get("lines", 0.0)))
            is_test = float(
                "test" in file_path.lower()
                or file_path.startswith("tests/")
                or "/test_" in file_path
            )

            row = [0.0] * NODE_FEATURE_DIM
            type_idx = self._type_index.get(node.node_type, 0)
            row[type_idx] = 1.0

            scalars = [
                is_changed,
                in_degree.get(node.node_id, 0) / max_degree,
                out_degree.get(node.node_id, 0) / max_degree,
                pagerank.get(node.node_id, 0.0),
                min(complexity / 50.0, 1.0),
                min(added / 200.0, 1.0),
                min(deleted / 200.0, 1.0),
                min(bug_counts.get(file_path, 0) / 10.0, 1.0),
                is_test,
                min(loc / 1000.0, 1.0),
                float(props.get("function_count", 0)) / 50.0,
                float(props.get("class_count", 0)) / 20.0,
                float(props.get("import_count", 0)) / 30.0,
                float(props.get("api_surface", 0)) / 10.0,
                float(props.get("db_access", 0)),
                float(props.get("mq_access", 0)),
                float(diff_result.complexity_delta / 20.0 if diff_result else 0.0),
                float(diff_result.deleted_code_ratio if diff_result else 0.0),
                min(len(diff_result.modified_functions) / 20.0, 1.0) if diff_result else 0.0,
                float(len(changed_files) / 20.0),
                float(node.node_type == NodeType.SERVICE),
                float(node.node_type == NodeType.MODULE),
                float("init" in file_path.lower()),
                float(file_path.endswith(".py")),
                float(file_path.endswith((".ts", ".tsx", ".js", ".jsx"))),
                float(props.get("is_entrypoint", 0)),
                float(props.get("has_tests", 0)),
            ]
            row[NODE_TYPE_COUNT : NODE_TYPE_COUNT + len(scalars)] = scalars[: NODE_FEATURE_DIM - NODE_TYPE_COUNT]
            rows.append(row)

        return np.asarray(rows, dtype=np.float32), node_ids, file_node_indices

    @staticmethod
    def _file_line_stats(diff_result: DiffAnalysisResult | None) -> dict[str, tuple[int, int]]:
        if not diff_result:
            return {}
        per_file: dict[str, tuple[int, int]] = defaultdict(lambda: (0, 0))
        # DiffAnalysisResult does not expose per-file stats; approximate from aggregate
        if diff_result.changed_files:
            share = max(diff_result.added_lines // len(diff_result.changed_files), 0)
            del_share = max(diff_result.deleted_lines // len(diff_result.changed_files), 0)
            for path in diff_result.changed_files:
                per_file[path] = (share, del_share)
        return per_file

    @staticmethod
    def _degrees(snapshot: GraphSnapshot) -> tuple[dict[str, int], dict[str, int]]:
        in_degree: dict[str, int] = defaultdict(int)
        out_degree: dict[str, int] = defaultdict(int)
        for edge in snapshot.edges:
            out_degree[edge.source_id] += 1
            in_degree[edge.target_id] += 1
        return in_degree, out_degree

    @staticmethod
    def _pagerank(snapshot: GraphSnapshot, nodes: list[GraphNode]) -> dict[str, float]:
        """Lightweight PageRank without networkx dependency at import time."""
        ids = [n.node_id for n in nodes]
        index = {nid: i for i, nid in enumerate(ids)}
        n = len(ids)
        if n == 0:
            return {}

        adj: list[list[int]] = [[] for _ in range(n)]
        for edge in snapshot.edges:
            if edge.source_id in index and edge.target_id in index:
                adj[index[edge.source_id]].append(index[edge.target_id])

        d = 0.85
        rank = [1.0 / n] * n
        for _ in range(20):
            new_rank = [(1 - d) / n] * n
            for i in range(n):
                if not adj[i]:
                    for j in range(n):
                        new_rank[j] += d * rank[i] / n
                else:
                    share = d * rank[i] / len(adj[i])
                    for j in adj[i]:
                        new_rank[j] += share
            rank = new_rank

        max_rank = max(rank) if rank else 1.0
        if max_rank <= 0:
            max_rank = 1.0
        return {ids[i]: rank[i] / max_rank for i in range(n)}
