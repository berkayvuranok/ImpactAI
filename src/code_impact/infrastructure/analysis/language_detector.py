"""Language detection from file extensions."""

from pathlib import PurePosixPath

LANGUAGE_MAP: dict[str, str] = {
    ".py": "python",
    ".pyi": "python",
    ".js": "javascript",
    ".jsx": "javascript",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".go": "go",
    ".rs": "rust",
    ".java": "java",
    ".kt": "kotlin",
    ".rb": "ruby",
    ".cs": "csharp",
    ".cpp": "cpp",
    ".c": "c",
    ".h": "c",
    ".hpp": "cpp",
    ".swift": "swift",
    ".php": "php",
}


def detect_language(file_path: str) -> str | None:
    suffix = PurePosixPath(file_path).suffix.lower()
    return LANGUAGE_MAP.get(suffix)


def is_supported_ast_language(language: str | None) -> bool:
    return language in {"python", "javascript", "typescript"}
