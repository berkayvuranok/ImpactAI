"""Orchestrates diff parsing, AST analysis, and complexity metrics."""

from __future__ import annotations

from dataclasses import replace

from code_impact.domain.services.analysis_types import EnrichedDiffAnalysisResult, FileChangeDetail
from code_impact.infrastructure.analysis.ast_analyzer import ASTAnalyzer
from code_impact.infrastructure.analysis.complexity_analyzer import ComplexityAnalyzer
from code_impact.infrastructure.analysis.diff_parser import DiffParser


class DiffAnalysisService:
    """Enriches raw diffs with AST and complexity data."""

    def __init__(
        self,
        diff_parser: DiffParser | None = None,
        ast_analyzer: ASTAnalyzer | None = None,
        complexity_analyzer: ComplexityAnalyzer | None = None,
    ) -> None:
        self._diff_parser = diff_parser or DiffParser()
        self._ast_analyzer = ast_analyzer or ASTAnalyzer()
        self._complexity = complexity_analyzer or ComplexityAnalyzer()

    async def analyze(
        self,
        diff: str,
        file_contents_before: dict[str, str] | None = None,
        file_contents_after: dict[str, str] | None = None,
    ) -> EnrichedDiffAnalysisResult:
        parsed = self._diff_parser.parse_full(diff)
        base = parsed.result
        file_contents_before = file_contents_before or {}
        file_contents_after = file_contents_after or {}

        enriched_files: list[FileChangeDetail] = []
        total_complexity_delta = 0.0
        dependency_changes: set[str] = set()
        languages: set[str] = set()

        for fc in parsed.file_changes:
            before_src = file_contents_before.get(fc.file_path, "")
            after_src = file_contents_after.get(fc.file_path, "")

            if fc.language:
                languages.add(fc.language)

            before_ast = self._ast_analyzer.analyze(before_src, fc.language)
            after_ast = self._ast_analyzer.analyze(after_src, fc.language)
            symbols = self._ast_analyzer.diff_symbols(before_ast, after_ast)

            cx_before, cx_after, cx_delta = self._complexity.compute_delta(
                before_src or None, after_src or None, fc.file_path
            )
            total_complexity_delta += cx_delta
            dependency_changes.update(symbols["imports_added"])
            dependency_changes.update(symbols["imports_removed"])

            enriched_files.append(
                replace(
                    fc,
                    functions_added=symbols["functions_added"],
                    functions_modified=symbols["functions_modified"],
                    functions_deleted=symbols["functions_deleted"],
                    classes_added=symbols["classes_added"],
                    classes_modified=symbols["classes_modified"],
                    complexity_before=cx_before,
                    complexity_after=cx_after,
                    complexity_delta=cx_delta,
                    imports_added=symbols["imports_added"],
                    imports_removed=symbols["imports_removed"],
                )
            )

        return EnrichedDiffAnalysisResult(
            changed_files=base.changed_files,
            added_lines=base.added_lines,
            deleted_lines=base.deleted_lines,
            modified_functions=base.modified_functions,
            renamed_files=base.renamed_files,
            complexity_delta=total_complexity_delta,
            deleted_code_ratio=base.deleted_code_ratio,
            raw_diff=base.raw_diff,
            file_changes=enriched_files,
            dependency_changes=sorted(dependency_changes),
            languages_affected=sorted(languages),
        )
