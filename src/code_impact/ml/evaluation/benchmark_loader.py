"""Load golden benchmark suites from JSON files."""

from __future__ import annotations

import json
from pathlib import Path

from code_impact.ml.evaluation.types import BenchmarkSample, BenchmarkSuite, GroundTruth


def load_benchmark(path: str | Path) -> BenchmarkSuite:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    samples = [
        BenchmarkSample(
            id=str(s["id"]),
            description=str(s.get("description", "")),
            diff=str(s["diff"]),
            ground_truth=GroundTruth(
                risk_score=float(s["ground_truth"]["risk_score"]),
                is_regression=bool(s["ground_truth"]["is_regression"]),
                affected_files=list(s["ground_truth"].get("affected_files", [])),
            ),
        )
        for s in raw.get("samples", [])
    ]
    return BenchmarkSuite(
        name=str(raw.get("name", Path(path).stem)),
        description=str(raw.get("description", "")),
        samples=samples,
    )


def default_benchmark_path(base_dir: str | Path) -> Path:
    return Path(base_dir) / "default.json"
