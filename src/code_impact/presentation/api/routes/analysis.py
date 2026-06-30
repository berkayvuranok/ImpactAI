"""Diff analysis endpoints."""

from fastapi import APIRouter

from code_impact.application.schemas import AnalyzeDiffRequest, AnalyzeDiffResponse, FileChangeResponse
from code_impact.application.use_cases import AnalyzeDiffCommand, AnalyzeDiffUseCase
from code_impact.presentation.api.dependencies import get_analyze_diff_use_case
from fastapi import Depends

router = APIRouter(prefix="/analyze")


@router.post("/diff", response_model=AnalyzeDiffResponse)
async def analyze_diff(
    body: AnalyzeDiffRequest,
    use_case: AnalyzeDiffUseCase = Depends(get_analyze_diff_use_case),
) -> AnalyzeDiffResponse:
    """
    Parse a unified diff and return structural analysis.

    Includes changed files, modified functions, AST symbols,
    cyclomatic complexity deltas, and dependency changes.
    """
    result = await use_case.execute(
        AnalyzeDiffCommand(
            diff=body.diff,
            file_contents_before=body.file_contents_before,
            file_contents_after=body.file_contents_after,
        )
    )

    return AnalyzeDiffResponse(
        changed_files=result.changed_files,
        added_lines=result.added_lines,
        deleted_lines=result.deleted_lines,
        modified_functions=result.modified_functions,
        renamed_files=result.renamed_files,
        complexity_delta=result.complexity_delta,
        deleted_code_ratio=result.deleted_code_ratio,
        dependency_changes=result.dependency_changes,
        languages_affected=result.languages_affected,
        file_changes=[
            FileChangeResponse(
                file_path=fc.file_path,
                change_type=fc.change_type,
                added_lines=fc.added_lines,
                deleted_lines=fc.deleted_lines,
                language=fc.language,
                old_path=fc.old_path,
                functions_added=fc.functions_added,
                functions_modified=fc.functions_modified,
                functions_deleted=fc.functions_deleted,
                classes_added=fc.classes_added,
                classes_modified=fc.classes_modified,
                complexity_before=fc.complexity_before,
                complexity_after=fc.complexity_after,
                complexity_delta=fc.complexity_delta,
                imports_added=fc.imports_added,
                imports_removed=fc.imports_removed,
            )
            for fc in result.file_changes
        ],
    )
