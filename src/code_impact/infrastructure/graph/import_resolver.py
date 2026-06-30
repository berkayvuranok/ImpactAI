"""Resolve import statements to repository file paths."""

from __future__ import annotations

import re
from pathlib import PurePosixPath


def parse_import_modules(import_line: str) -> list[str]:
    line = import_line.strip()
    modules: list[str] = []

    if line.startswith("from "):
        match = re.match(r"from\s+([\w.]+)\s+import", line)
        if match:
            modules.append(match.group(1))
    elif line.startswith("import "):
        rest = line.removeprefix("import ").split("#")[0].strip()
        for part in rest.split(","):
            part = part.strip().split(" as ")[0].strip()
            if part:
                modules.append(part)

    return modules


def resolve_module_to_file(module: str, file_paths: set[str]) -> str | None:
    """Best-effort resolution of a module name to a file in the repo."""
    module_path = module.replace(".", "/")

    candidates = [
        f"{module_path}.py",
        f"{module_path}/__init__.py",
        f"src/{module_path}.py",
        f"src/{module_path}/__init__.py",
        f"lib/{module_path}.py",
        f"app/{module_path}.py",
    ]

    for candidate in candidates:
        if candidate in file_paths:
            return candidate

    suffix = PurePosixPath(module_path).name
    matches = [p for p in file_paths if PurePosixPath(p).name in (f"{suffix}.py", f"{suffix}.ts", f"{suffix}.js")]
    if len(matches) == 1:
        return matches[0]

    return None
