"""Source file filtering for graph construction."""

SOURCE_EXTENSIONS = frozenset({
    ".py",
    ".pyi",
    ".js",
    ".jsx",
    ".ts",
    ".tsx",
    ".go",
    ".java",
    ".kt",
    ".rs",
    ".rb",
    ".cs",
    ".cpp",
    ".c",
    ".h",
    ".hpp",
    ".swift",
    ".php",
})

SKIP_DIRS = frozenset({
    ".git",
    "node_modules",
    "__pycache__",
    ".venv",
    "venv",
    "dist",
    "build",
    ".tox",
    "coverage",
    ".pytest_cache",
    "target",
})


def is_source_file(path: str) -> bool:
    lower = path.lower()
    if any(part in SKIP_DIRS for part in lower.split("/")):
        return False
    return any(lower.endswith(ext) for ext in SOURCE_EXTENSIONS)
