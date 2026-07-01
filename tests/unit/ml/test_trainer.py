"""Tests for GNN trainer and model registry."""

from pathlib import Path

import pytest

torch = pytest.importorskip("torch")

from support.ml_fixtures import sample_training_sample

from code_impact.ml.model_registry import FileModelRegistry, load_artifact, save_artifact, ModelArtifact
from code_impact.ml.models.code_impact_gnn import GNNConfig
from code_impact.ml.training.trainer import GNNTrainer, TrainConfig


def test_trainer_saves_artifact(tmp_path: Path):
    samples = [sample_training_sample(True), sample_training_sample(False)]
    output = tmp_path / "model.pt"
    trainer = GNNTrainer(train_config=TrainConfig(epochs=2, device="cpu"))
    result = trainer.train(samples, samples[:1], output_path=output)
    assert Path(result.artifact_path).exists()
    model, config, metrics = load_artifact(result.artifact_path)
    assert config.in_channels > 0
    assert "risk_rmse" in metrics


def test_file_model_registry(tmp_path: Path):
    registry = FileModelRegistry(str(tmp_path))
    record = registry.register("code_impact_gnn", "/tmp/model.pt", {"f1": 0.5})
    active = registry.get_active("code_impact_gnn")
    assert active is not None
    assert active.version == record.version
