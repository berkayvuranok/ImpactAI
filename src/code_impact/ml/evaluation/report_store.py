"""Persist evaluation reports to disk."""

from __future__ import annotations

import json
from pathlib import Path
from uuid import UUID

from code_impact.ml.evaluation.types import EvaluationReport


class EvaluationReportStore:
    def __init__(self, storage_path: str | Path) -> None:
        self._root = Path(storage_path)
        self._root.mkdir(parents=True, exist_ok=True)

    def save(self, report: EvaluationReport) -> Path:
        path = self._root / f"{report.id}.json"
        path.write_text(json.dumps(report.to_dict(), indent=2), encoding="utf-8")
        return path

    def get(self, report_id: UUID) -> EvaluationReport | None:
        path = self._root / f"{report_id}.json"
        if not path.exists():
            return None
        return EvaluationReport.from_dict(json.loads(path.read_text(encoding="utf-8")))

    def list_reports(self, limit: int = 20) -> list[EvaluationReport]:
        files = sorted(self._root.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
        reports: list[EvaluationReport] = []
        for path in files[:limit]:
            reports.append(EvaluationReport.from_dict(json.loads(path.read_text(encoding="utf-8"))))
        return reports
