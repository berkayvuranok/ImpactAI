"""Unit tests for DiffParser."""

import subprocess
from pathlib import Path

import pytest

from code_impact.infrastructure.analysis.diff_parser import DiffParser


@pytest.fixture
def parser() -> DiffParser:
    return DiffParser()


@pytest.fixture
def sample_diff(tmp_path: Path) -> str:
    """Generate a valid unified diff from a real git repository."""
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "t@e.com"], cwd=repo, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "T"], cwd=repo, check=True, capture_output=True)

    calc = repo / "src" / "calculator.py"
    calc.parent.mkdir(parents=True)
    calc.write_text(
        "class Calculator:\n"
        "    def add(self, a, b):\n"
        "        return a + b\n"
    )
    subprocess.run(["git", "add", "."], cwd=repo, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=repo, check=True, capture_output=True)

    calc.write_text(
        "class Calculator:\n"
        "    def add(self, a, b, c=0):\n"
        "        return a + b\n"
        "\n"
        "    def multiply(self, a, b):\n"
        "        return a * b\n"
    )

    result = subprocess.run(
        ["git", "diff", "HEAD", "--", "src/calculator.py"],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout


class TestDiffParser:
    def test_parse_changed_files(self, parser: DiffParser, sample_diff: str):
        parsed = parser.parse_full(sample_diff)
        assert "src/calculator.py" in parsed.result.changed_files

    def test_parse_new_file(self, parser: DiffParser):
        new_file_diff = """\
diff --git a/README.md b/README.md
new file mode 100644
--- /dev/null
+++ b/README.md
@@ -0,0 +1,2 @@
+# Test
+Project
"""
        parsed = parser.parse_full(new_file_diff)
        assert "README.md" in parsed.result.changed_files
        assert parsed.file_changes[0].change_type == "added"

    def test_parse_line_counts(self, parser: DiffParser, sample_diff: str):
        parsed = parser.parse_full(sample_diff)
        assert parsed.result.added_lines > 0
        assert parsed.result.deleted_lines > 0

    def test_parse_modified_functions(self, parser: DiffParser, sample_diff: str):
        parsed = parser.parse_full(sample_diff)
        assert any("multiply" in fn for fn in parsed.result.modified_functions)

    def test_parse_file_change_details(self, parser: DiffParser, sample_diff: str):
        parsed = parser.parse_full(sample_diff)
        calc = next(fc for fc in parsed.file_changes if "calculator" in fc.file_path)
        assert calc.change_type == "modified"
        assert calc.language == "python"

    def test_empty_diff(self, parser: DiffParser):
        parsed = parser.parse_full("")
        assert parsed.result.changed_files == []
        assert parsed.result.added_lines == 0

    @pytest.mark.asyncio
    async def test_async_parse(self, parser: DiffParser, sample_diff: str):
        result = await parser.parse(sample_diff)
        assert any("calculator" in f for f in result.changed_files)
