"""Persist graph snapshots as JSON on disk."""

from __future__ import annotations

import json
from pathlib import Path
from uuid import UUID, uuid4

from code_impact.domain.entities import GraphEdge, GraphNode, GraphSnapshot
from code_impact.domain.value_objects.enums import EdgeType, NodeType


class GraphStorage:
    def __init__(self, base_path: str) -> None:
        self._base = Path(base_path)
        self._base.mkdir(parents=True, exist_ok=True)

    def save(self, snapshot: GraphSnapshot) -> str:
        repo_dir = self._base / str(snapshot.repository_id)
        repo_dir.mkdir(parents=True, exist_ok=True)
        path = repo_dir / f"{snapshot.commit_sha[:12]}.json"

        payload = {
            "snapshot_id": str(snapshot.id),
            "repository_id": str(snapshot.repository_id),
            "commit_sha": snapshot.commit_sha,
            "node_count": snapshot.node_count,
            "edge_count": snapshot.edge_count,
            "nodes": [
                {
                    "node_id": n.node_id,
                    "node_type": n.node_type.value,
                    "name": n.name,
                    "file_path": n.file_path,
                    "properties": n.properties,
                }
                for n in snapshot.nodes
            ],
            "edges": [
                {
                    "source_id": e.source_id,
                    "target_id": e.target_id,
                    "edge_type": e.edge_type.value,
                    "weight": e.weight,
                    "properties": e.properties,
                }
                for e in snapshot.edges
            ],
        }
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return str(path)

    def load(self, repository_id: UUID, commit_sha: str) -> GraphSnapshot | None:
        repo_dir = self._base / str(repository_id)
        path = repo_dir / f"{commit_sha[:12]}.json"
        if not path.exists() and repo_dir.exists():
            matches = [p for p in repo_dir.glob("*.json") if commit_sha.startswith(p.stem)]
            path = matches[0] if matches else path
        if not path.exists():
            return None

        data = json.loads(path.read_text(encoding="utf-8"))
        snapshot_id = UUID(data["snapshot_id"])
        nodes = [
            GraphNode(
                id=uuid4(),
                snapshot_id=snapshot_id,
                node_id=n["node_id"],
                node_type=NodeType(n["node_type"]),
                name=n["name"],
                file_path=n.get("file_path"),
                properties=n.get("properties", {}),
            )
            for n in data["nodes"]
        ]
        edges = [
            GraphEdge(
                id=uuid4(),
                snapshot_id=snapshot_id,
                source_id=e["source_id"],
                target_id=e["target_id"],
                edge_type=EdgeType(e["edge_type"]),
                weight=e.get("weight", 1.0),
                properties=e.get("properties", {}),
            )
            for e in data["edges"]
        ]
        return GraphSnapshot(
            id=snapshot_id,
            repository_id=UUID(data["repository_id"]),
            commit_sha=data["commit_sha"],
            node_count=data["node_count"],
            edge_count=data["edge_count"],
            storage_path=str(path),
            nodes=nodes,
            edges=edges,
        )
