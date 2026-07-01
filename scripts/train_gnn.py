#!/usr/bin/env python3
"""Offline GNN training CLI."""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path
from uuid import UUID

# Allow running as `python scripts/train_gnn.py`
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from code_impact.infrastructure.config.settings import get_settings
from code_impact.infrastructure.embeddings.mock_embedding_service import MockEmbeddingService
from code_impact.infrastructure.git.git_service import GitService
from code_impact.infrastructure.persistence.database import create_session_factory
from code_impact.infrastructure.persistence.repositories import (
    SqlAlchemyCommitRepository,
    SqlAlchemyGraphRepository,
)
from code_impact.ml.model_registry import FileModelRegistry
from code_impact.ml.training.sample_builder import TrainingDatasetBuilder
from code_impact.ml.training.trainer import GNNTrainer, TrainConfig


async def _train(repository_id: UUID, epochs: int, output: str, device: str) -> None:
    settings = get_settings()
    session_factory = create_session_factory(settings)
    git = GitService(settings.git_storage_path, settings.max_repo_size_mb)
    embeddings = MockEmbeddingService()

    async with session_factory() as session:
        builder = TrainingDatasetBuilder(
            git_service=git,
            commit_repo=SqlAlchemyCommitRepository(session),
            graph_repo=SqlAlchemyGraphRepository(session),
            embedding_service=embeddings,
        )
        samples = await builder.build_for_repository(repository_id)
        if len(samples) < 2:
            print("Not enough training samples; need synced commits + graph snapshots.")
            return

        split = max(len(samples) // 5, 1)
        val = samples[:split]
        train = samples[split:]

    trainer = GNNTrainer(train_config=TrainConfig(epochs=epochs, device=device))
    result = trainer.train(train, val, output_path=output)

    registry = FileModelRegistry(settings.model_storage_path)
    registry.register("code_impact_gnn", result.artifact_path, result.metrics, activate=True)
    print(f"Training complete: {result.artifact_path}")
    print(f"Metrics: {result.metrics}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Train CodeImpactGNN on repository history")
    parser.add_argument("--repository-id", required=True, help="Repository UUID")
    parser.add_argument("--epochs", type=int, default=10)
    parser.add_argument("--output", default="models/gnn/latest.pt")
    parser.add_argument("--device", default="cpu")
    args = parser.parse_args()
    asyncio.run(_train(UUID(args.repository_id), args.epochs, args.output, args.device))


if __name__ == "__main__":
    main()
