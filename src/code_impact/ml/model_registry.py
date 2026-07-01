"""Model artifact persistence and registry."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID, uuid4

import torch

from code_impact.ml.models.code_impact_gnn import CodeImpactGNN, GNNConfig


@dataclass(frozen=True, slots=True)
class ModelArtifact:
    model_state: dict
    gnn_config: GNNConfig
    metrics: dict[str, float]
    version: str = "1.0.0"
    trained_at: str = ""

    def __post_init__(self) -> None:
        if not self.trained_at:
            object.__setattr__(self, "trained_at", datetime.now(UTC).isoformat())


@dataclass
class RegisteredModel:
    id: UUID
    name: str
    version: str
    model_type: str
    artifact_path: str
    metrics: dict
    is_active: bool
    trained_at: datetime


def save_artifact(artifact: ModelArtifact, path: str | Path) -> Path:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "version": artifact.version,
        "trained_at": artifact.trained_at,
        "gnn_config": asdict(artifact.gnn_config),
        "metrics": artifact.metrics,
        "model_state": artifact.model_state,
    }
    torch.save(payload, out)
    meta_path = out.with_suffix(".meta.json")
    meta_path.write_text(
        json.dumps(
            {
                "version": artifact.version,
                "trained_at": artifact.trained_at,
                "metrics": artifact.metrics,
                "gnn_config": asdict(artifact.gnn_config),
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return out


def load_artifact(path: str | Path) -> tuple[CodeImpactGNN, GNNConfig, dict[str, float]]:
    payload = torch.load(path, map_location="cpu", weights_only=False)
    config = GNNConfig(**payload["gnn_config"])
    model = CodeImpactGNN(config)
    model.load_state_dict(payload["model_state"])
    metrics = payload.get("metrics", {})
    return model, config, metrics


class FileModelRegistry:
    """Filesystem-backed registry; DB persistence added via IModelRepository."""

    def __init__(self, base_path: str) -> None:
        self._base = Path(base_path)
        self._base.mkdir(parents=True, exist_ok=True)
        self._index_path = self._base / "registry.json"
        if not self._index_path.exists():
            self._index_path.write_text("[]", encoding="utf-8")

    def register(
        self,
        name: str,
        artifact_path: str,
        metrics: dict[str, float],
        model_type: str = "gnn",
        activate: bool = True,
    ) -> RegisteredModel:
        entries = self._load_index()
        version = str(len([e for e in entries if e["name"] == name]) + 1)
        if activate:
            for entry in entries:
                if entry["name"] == name:
                    entry["is_active"] = False

        record = RegisteredModel(
            id=uuid4(),
            name=name,
            version=version,
            model_type=model_type,
            artifact_path=artifact_path,
            metrics=metrics,
            is_active=activate,
            trained_at=datetime.now(UTC),
        )
        entries.append(
            {
                "id": str(record.id),
                "name": record.name,
                "version": record.version,
                "model_type": record.model_type,
                "artifact_path": record.artifact_path,
                "metrics": record.metrics,
                "is_active": record.is_active,
                "trained_at": record.trained_at.isoformat(),
            }
        )
        self._index_path.write_text(json.dumps(entries, indent=2), encoding="utf-8")
        return record

    def get_active(self, name: str) -> RegisteredModel | None:
        for entry in self._load_index():
            if entry["name"] == name and entry.get("is_active"):
                return RegisteredModel(
                    id=UUID(entry["id"]),
                    name=entry["name"],
                    version=entry["version"],
                    model_type=entry["model_type"],
                    artifact_path=entry["artifact_path"],
                    metrics=entry.get("metrics", {}),
                    is_active=True,
                    trained_at=datetime.fromisoformat(entry["trained_at"]),
                )
        return None

    def _load_index(self) -> list[dict]:
        return json.loads(self._index_path.read_text(encoding="utf-8"))
