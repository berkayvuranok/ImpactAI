"""Deep structure extraction: calls, inheritance, external deps."""

from __future__ import annotations

import re

from code_impact.domain.services.analysis_types import StructureAnalysisResult
from code_impact.infrastructure.analysis.ast_analyzer import ASTAnalyzer
from code_impact.infrastructure.graph.edge_detectors import (
    detect_api_targets,
    detect_db_targets,
    detect_mq_targets,
)


class StructureAnalyzer:
    def __init__(self, ast_analyzer: ASTAnalyzer | None = None) -> None:
        self._ast = ast_analyzer or ASTAnalyzer()

    def analyze(self, source_code: str, language: str | None) -> StructureAnalysisResult:
        base = self._ast.analyze(source_code, language)
        calls = self._extract_calls(source_code, base, language)
        inheritance = self._extract_inheritance(source_code, language)

        return StructureAnalysisResult(
            language=base.language,
            functions=base.functions,
            classes=base.classes,
            imports=base.imports,
            total_complexity=base.total_complexity,
            calls=calls,
            inheritance=inheritance,
            api_targets=detect_api_targets(source_code),
            db_targets=detect_db_targets(source_code),
            mq_targets=detect_mq_targets(source_code),
        )

    def _extract_calls(
        self, source: str, ast_result, language: str | None
    ) -> list[tuple[str, str]]:
        calls: list[tuple[str, str]] = []
        current_fn = "<module>"

        for i, line in enumerate(source.splitlines(), start=1):
            stripped = line.strip()
            if language == "python":
                fn_match = re.match(r"^(?:async\s+)?def\s+(\w+)\s*\(", stripped)
                if fn_match:
                    current_fn = fn_match.group(1)
            else:
                fn_match = re.match(r"^(?:export\s+)?(?:async\s+)?function\s+(\w+)", stripped)
                if fn_match:
                    current_fn = fn_match.group(1)

            for match in re.finditer(r"\b([A-Za-z_][\w]*(?:\.[A-Za-z_][\w]*)*)\s*\(", stripped):
                callee = match.group(1)
                if callee in ("if", "while", "for", "switch", "catch", "def", "class", "return"):
                    continue
                calls.append((current_fn, callee))

        for fn in ast_result.functions:
            if fn.qualified_name != fn.name:
                calls.append((fn.qualified_name.split(".")[0], fn.name))

        return list(dict.fromkeys(calls))

    def _extract_inheritance(
        self, source: str, language: str | None
    ) -> list[tuple[str, list[str]]]:
        inheritance: list[tuple[str, list[str]]] = []

        if language == "python":
            for line in source.splitlines():
                match = re.match(r"^class\s+(\w+)\s*\(([^)]+)\)", line.strip())
                if match:
                    class_name = match.group(1)
                    bases = [b.strip().split(".")[-1] for b in match.group(2).split(",") if b.strip()]
                    inheritance.append((class_name, bases))
        else:
            for line in source.splitlines():
                match = re.match(r"^(?:export\s+)?class\s+(\w+)\s+extends\s+(\w+)", line.strip())
                if match:
                    inheritance.append((match.group(1), [match.group(2)]))

        return inheritance
