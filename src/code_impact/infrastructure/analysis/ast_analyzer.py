"""AST extraction via Tree-sitter with regex fallback."""

from __future__ import annotations

import re
from dataclasses import replace

from code_impact.domain.services.analysis_types import (
    ASTAnalysisResult,
    ClassInfo,
    FunctionInfo,
)
from code_impact.infrastructure.analysis.complexity_analyzer import ComplexityAnalyzer
from code_impact.infrastructure.analysis.language_detector import is_supported_ast_language

# Tree-sitter language bindings (optional at runtime)
_TS_LANGUAGES: dict[str, object] = {}


def _load_tree_sitter_language(language: str):
    if language in _TS_LANGUAGES:
        return _TS_LANGUAGES[language]
    try:
        from tree_sitter import Language

        if language == "python":
            import tree_sitter_python as lang_module

            lang = Language(lang_module.language())
        elif language == "javascript":
            import tree_sitter_javascript as lang_module

            lang = Language(lang_module.language())
        elif language == "typescript":
            import tree_sitter_typescript as lang_module

            lang = Language(lang_module.language_typescript())
        else:
            return None
        _TS_LANGUAGES[language] = lang
        return lang
    except Exception:
        return None


class ASTAnalyzer:
    def __init__(self) -> None:
        self._complexity = ComplexityAnalyzer()

    def analyze(self, source_code: str, language: str | None) -> ASTAnalysisResult:
        if not source_code.strip() or not language:
            return ASTAnalysisResult(language=language or "unknown", functions=[], classes=[], imports=[], total_complexity=0.0)

        if is_supported_ast_language(language) and _load_tree_sitter_language(language):
            try:
                return self._analyze_tree_sitter(source_code, language)
            except Exception:
                pass

        return self._analyze_regex(source_code, language)

    def _analyze_tree_sitter(self, source_code: str, language: str) -> ASTAnalysisResult:
        from tree_sitter import Parser

        lang = _load_tree_sitter_language(language)
        parser = Parser(lang)
        tree = parser.parse(source_code.encode("utf-8"))
        root = tree.root_node

        functions: list[FunctionInfo] = []
        classes: list[ClassInfo] = []
        imports: list[str] = []

        def walk(node, class_prefix: str = "") -> None:
            ntype = node.type
            if ntype in ("function_definition", "function_declaration", "method_definition"):
                name_node = node.child_by_field_name("name")
                if name_node:
                    name = source_code[name_node.start_byte : name_node.end_byte]
                    qualified = f"{class_prefix}.{name}" if class_prefix else name
                    functions.append(
                        FunctionInfo(
                            name=name,
                            qualified_name=qualified,
                            start_line=node.start_point[0] + 1,
                            end_line=node.end_point[0] + 1,
                        )
                    )
            elif ntype in ("class_definition", "class_declaration"):
                name_node = node.child_by_field_name("name")
                if name_node:
                    name = source_code[name_node.start_byte : name_node.end_byte]
                    classes.append(
                        ClassInfo(
                            name=name,
                            qualified_name=name,
                            start_line=node.start_point[0] + 1,
                            end_line=node.end_point[0] + 1,
                        )
                    )
                    class_prefix = name
            elif ntype in ("import_statement", "import_from_statement"):
                imports.append(source_code[node.start_byte : node.end_byte].strip())

            for child in node.children:
                walk(child, class_prefix)

        walk(root)

        total_complexity = self._complexity.compute_complexity(source_code, language)
        fn_with_cx = [
            replace(fn, complexity=total_complexity / max(len(functions), 1)) for fn in functions
        ]

        return ASTAnalysisResult(
            language=language,
            functions=fn_with_cx,
            classes=classes,
            imports=imports,
            total_complexity=total_complexity,
        )

    def _analyze_regex(self, source_code: str, language: str) -> ASTAnalysisResult:
        functions: list[FunctionInfo] = []
        classes: list[ClassInfo] = []
        imports: list[str] = []

        if language == "python":
            for i, line in enumerate(source_code.splitlines(), start=1):
                stripped = line.strip()
                fn_match = re.match(r"^(?:async\s+)?def\s+(\w+)\s*\(", stripped)
                if fn_match:
                    functions.append(
                        FunctionInfo(fn_match.group(1), fn_match.group(1), i, i)
                    )
                cls_match = re.match(r"^class\s+(\w+)", stripped)
                if cls_match:
                    classes.append(
                        ClassInfo(cls_match.group(1), cls_match.group(1), i, i)
                    )
                if stripped.startswith(("import ", "from ")):
                    imports.append(stripped)
        else:
            for i, line in enumerate(source_code.splitlines(), start=1):
                stripped = line.strip()
                fn_match = re.match(
                    r"^(?:export\s+)?(?:async\s+)?function\s+(\w+)", stripped
                )
                if fn_match:
                    functions.append(
                        FunctionInfo(fn_match.group(1), fn_match.group(1), i, i)
                    )
                cls_match = re.match(r"^(?:export\s+)?class\s+(\w+)", stripped)
                if cls_match:
                    classes.append(
                        ClassInfo(cls_match.group(1), cls_match.group(1), i, i)
                    )
                if stripped.startswith("import "):
                    imports.append(stripped)

        total_complexity = self._complexity.compute_complexity(source_code, language)
        return ASTAnalysisResult(
            language=language,
            functions=functions,
            classes=classes,
            imports=imports,
            total_complexity=total_complexity,
        )

    def diff_symbols(
        self,
        before: ASTAnalysisResult,
        after: ASTAnalysisResult,
    ) -> dict[str, list[str]]:
        before_fns = {f.qualified_name for f in before.functions}
        after_fns = {f.qualified_name for f in after.functions}
        before_cls = {c.qualified_name for c in before.classes}
        after_cls = {c.qualified_name for c in after.classes}

        return {
            "functions_added": sorted(after_fns - before_fns),
            "functions_deleted": sorted(before_fns - after_fns),
            "functions_modified": sorted(
                fn for fn in before_fns & after_fns
                if self._symbol_changed(fn, before, after)
            ),
            "classes_added": sorted(after_cls - before_cls),
            "classes_modified": sorted(before_cls & after_cls),
            "imports_added": sorted(set(after.imports) - set(before.imports)),
            "imports_removed": sorted(set(before.imports) - set(after.imports)),
        }

    @staticmethod
    def _symbol_changed(name: str, before: ASTAnalysisResult, after: ASTAnalysisResult) -> bool:
        b = next((f for f in before.functions if f.qualified_name == name), None)
        a = next((f for f in after.functions if f.qualified_name == name), None)
        if b and a:
            return (b.start_line, b.end_line) != (a.start_line, a.end_line)
        return False
