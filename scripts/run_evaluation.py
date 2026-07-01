#!/usr/bin/env python3
"""Run golden benchmark evaluation from the command line."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from code_impact.application.services.benchmark_evaluation_service import BenchmarkEvaluationService
from code_impact.ml.evaluation.report_store import EvaluationReportStore


async def main() -> None:
    name = sys.argv[1] if len(sys.argv) > 1 else "default"
    out_dir = ROOT / "data" / "evaluations"
    service = BenchmarkEvaluationService(
        EvaluationReportStore(out_dir),
        benchmark_dir=str(ROOT / "data" / "benchmarks"),
    )
    report = await service.run_named_benchmark(name)
    print(f"Report ID: {report.id}")
    print(f"Passed: {report.passed}")
    print(f"Metrics: {report.aggregate_metrics}")


if __name__ == "__main__":
    asyncio.run(main())
