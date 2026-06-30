"""Unified diff parser using unidiff."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import PurePosixPath

from unidiff import PatchSet
from unidiff.errors import UnidiffParseError

from code_impact.domain.exceptions import ValidationError
from code_impact.domain.services import DiffAnalysisResult, IDiffParser
from code_impact.domain.services.analysis_types import FileChangeDetail
from code_impact.infrastructure.analysis.language_detector import detect_language

HUNK_FUNCTION_PATTERN = re.compile(
    r"^(?:@@ .+ @@\s*)?(?:def |class |function |async function |export (?:default )?(?:function|class) )(.+)$"
)


@dataclass
class ParsedDiff:
    result: DiffAnalysisResult
    file_changes: list[FileChangeDetail]


class DiffParser(IDiffParser):
    async def parse(self, diff: str) -> DiffAnalysisResult:
        return self.parse_full(diff).result

    def parse_sync(self, diff: str) -> DiffAnalysisResult:
        return self.parse_full(diff).result

    def parse_full(self, diff: str) -> ParsedDiff:
        if not diff.strip():
            empty = DiffAnalysisResult(
                changed_files=[],
                added_lines=0,
                deleted_lines=0,
                modified_functions=[],
                renamed_files={},
                complexity_delta=0.0,
                deleted_code_ratio=0.0,
                raw_diff=diff,
            )
            return ParsedDiff(result=empty, file_changes=[])

        try:
            patch_set = PatchSet(diff if diff.endswith("\n") else diff + "\n")
        except UnidiffParseError as exc:
            raise ValidationError(f"Invalid unified diff: {exc}") from exc

        changed_files: list[str] = []
        renamed_files: dict[str, str] = {}
        file_changes: list[FileChangeDetail] = []
        modified_functions: list[str] = []
        total_added = 0
        total_deleted = 0

        for patched_file in patch_set:
            target_path = patched_file.path
            source_path = (
                patched_file.source_file.removeprefix("a/") if patched_file.source_file else None
            )

            if patched_file.is_removed_file:
                change_type = "deleted"
                file_path = source_path or target_path
            elif patched_file.is_added_file:
                change_type = "added"
                file_path = target_path
            elif patched_file.is_rename:
                change_type = "renamed"
                file_path = target_path
                if source_path:
                    renamed_files[source_path] = target_path
            else:
                change_type = "modified"
                file_path = target_path

            added = patched_file.added
            deleted = patched_file.removed
            total_added += added
            total_deleted += deleted
            changed_files.append(file_path)

            file_functions = self._extract_functions_from_hunks(patched_file)
            modified_functions.extend(f"{file_path}::{fn}" for fn in file_functions)

            file_changes.append(
                FileChangeDetail(
                    file_path=file_path,
                    change_type=change_type,
                    added_lines=added,
                    deleted_lines=deleted,
                    language=detect_language(file_path),
                    old_path=source_path if change_type == "renamed" else None,
                    functions_modified=file_functions,
                )
            )

        total_lines = total_added + total_deleted
        deleted_ratio = total_deleted / total_lines if total_lines > 0 else 0.0

        result = DiffAnalysisResult(
            changed_files=changed_files,
            added_lines=total_added,
            deleted_lines=total_deleted,
            modified_functions=list(dict.fromkeys(modified_functions)),
            renamed_files=renamed_files,
            complexity_delta=0.0,
            deleted_code_ratio=deleted_ratio,
            raw_diff=diff,
        )
        return ParsedDiff(result=result, file_changes=file_changes)

    def _extract_functions_from_hunks(self, patched_file) -> list[str]:
        functions: list[str] = []
        for hunk in patched_file:
            for line in hunk:
                if not line.is_added and not line.is_removed:
                    continue
                text = line.value.strip()
                match = HUNK_FUNCTION_PATTERN.match(text)
                if match:
                    functions.append(match.group(1).split("(")[0].strip())
        return functions

    @staticmethod
    def normalize_path(path: str) -> str:
        return str(PurePosixPath(path.replace("\\", "/")))
