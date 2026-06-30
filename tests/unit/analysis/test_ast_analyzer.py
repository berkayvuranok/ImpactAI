"""Unit tests for ASTAnalyzer."""

import pytest

from code_impact.infrastructure.analysis.ast_analyzer import ASTAnalyzer

PYTHON_SOURCE = '''
import os
from typing import List

class DataProcessor:
    def process(self, items: List[str]) -> int:
        count = 0
        for item in items:
            if item:
                count += 1
        return count

def helper():
    return True
'''

PYTHON_AFTER = '''
import os
import json
from typing import List

class DataProcessor:
    def process(self, items: List[str]) -> int:
        count = 0
        for item in items:
            if item and len(item) > 0:
                count += 1
        return count

    def validate(self, item: str) -> bool:
        return bool(item)

def helper():
    return True
'''


@pytest.fixture
def analyzer() -> ASTAnalyzer:
    return ASTAnalyzer()


class TestASTAnalyzer:
    def test_extract_python_functions(self, analyzer: ASTAnalyzer):
        result = analyzer.analyze(PYTHON_SOURCE, "python")
        fn_names = {f.name for f in result.functions}
        assert "process" in fn_names
        assert "helper" in fn_names

    def test_extract_python_classes(self, analyzer: ASTAnalyzer):
        result = analyzer.analyze(PYTHON_SOURCE, "python")
        assert any(c.name == "DataProcessor" for c in result.classes)

    def test_extract_imports(self, analyzer: ASTAnalyzer):
        result = analyzer.analyze(PYTHON_SOURCE, "python")
        assert len(result.imports) >= 2

    def test_complexity_positive(self, analyzer: ASTAnalyzer):
        result = analyzer.analyze(PYTHON_SOURCE, "python")
        assert result.total_complexity > 0

    def test_diff_symbols(self, analyzer: ASTAnalyzer):
        before = analyzer.analyze(PYTHON_SOURCE, "python")
        after = analyzer.analyze(PYTHON_AFTER, "python")
        diff = analyzer.diff_symbols(before, after)
        assert "validate" in diff["functions_added"]
        assert any("json" in imp for imp in diff["imports_added"])

    def test_javascript_regex_fallback(self, analyzer: ASTAnalyzer):
        js = "export function compute(x) { return x + 1; }\nexport class Engine {}"
        result = analyzer.analyze(js, "javascript")
        assert any(f.name == "compute" for f in result.functions)
        assert any(c.name == "Engine" for c in result.classes)
