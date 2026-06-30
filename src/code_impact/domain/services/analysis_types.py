"""Extended analysis result types."""

from dataclasses import dataclass, field

from code_impact.domain.services import DiffAnalysisResult  # noqa: F401 — re-export


@dataclass(frozen=True, slots=True)
class FunctionInfo:
    name: str
    qualified_name: str
    start_line: int
    end_line: int
    complexity: float | None = None


@dataclass(frozen=True, slots=True)
class ClassInfo:
    name: str
    qualified_name: str
    start_line: int
    end_line: int


@dataclass(frozen=True, slots=True)
class ASTAnalysisResult:
    language: str
    functions: list[FunctionInfo]
    classes: list[ClassInfo]
    imports: list[str]
    total_complexity: float


@dataclass(frozen=True, slots=True)
class StructureAnalysisResult:
    """Extended AST with call graph and external dependency signals."""

    language: str
    functions: list[FunctionInfo]
    classes: list[ClassInfo]
    imports: list[str]
    total_complexity: float
    calls: list[tuple[str, str]] = field(default_factory=list)
    inheritance: list[tuple[str, list[str]]] = field(default_factory=list)
    api_targets: list[str] = field(default_factory=list)
    db_targets: list[str] = field(default_factory=list)
    mq_targets: list[str] = field(default_factory=list)


@dataclass(frozen=True, slots=True)
class FileChangeDetail:
    file_path: str
    change_type: str
    added_lines: int
    deleted_lines: int
    language: str | None
    old_path: str | None = None
    functions_added: list[str] = field(default_factory=list)
    functions_modified: list[str] = field(default_factory=list)
    functions_deleted: list[str] = field(default_factory=list)
    classes_added: list[str] = field(default_factory=list)
    classes_modified: list[str] = field(default_factory=list)
    complexity_before: float | None = None
    complexity_after: float | None = None
    complexity_delta: float = 0.0
    imports_added: list[str] = field(default_factory=list)
    imports_removed: list[str] = field(default_factory=list)


@dataclass
class EnrichedDiffAnalysisResult(DiffAnalysisResult):
    """Diff analysis enriched with per-file AST and complexity metrics."""

    file_changes: list[FileChangeDetail] = field(default_factory=list)
    dependency_changes: list[str] = field(default_factory=list)
    languages_affected: list[str] = field(default_factory=list)
