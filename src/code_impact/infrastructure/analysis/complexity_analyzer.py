"""Cyclomatic complexity analysis."""

from __future__ import annotations

from code_impact.infrastructure.analysis.language_detector import detect_language


class ComplexityAnalyzer:
    def compute_complexity(self, source_code: str, language: str | None) -> float:
        if not source_code.strip():
            return 0.0
        if language == "python":
            return self._python_complexity(source_code)
        return self._approximate_complexity(source_code)

    def _python_complexity(self, source_code: str) -> float:
        try:
            from radon.complexity import cc_visit

            blocks = cc_visit(source_code)
            return sum(block.complexity for block in blocks)
        except Exception:
            return self._approximate_complexity(source_code)

    def _approximate_complexity(self, source_code: str) -> float:
        """Language-agnostic complexity proxy based on branch points."""
        keywords = (
            "if ",
            "elif ",
            "else ",
            "for ",
            "while ",
            "case ",
            "catch ",
            "&&",
            "||",
            "?",
        )
        count = 1
        for kw in keywords:
            count += source_code.count(kw)
        return float(count)

    def compute_delta(
        self,
        before: str | None,
        after: str | None,
        file_path: str,
    ) -> tuple[float | None, float | None, float]:
        language = detect_language(file_path)
        before_cx = self.compute_complexity(before or "", language) if before else None
        after_cx = self.compute_complexity(after or "", language) if after else None
        if before_cx is not None and after_cx is not None:
            return before_cx, after_cx, after_cx - before_cx
        if after_cx is not None:
            return before_cx, after_cx, after_cx
        if before_cx is not None:
            return before_cx, after_cx, -before_cx
        return None, None, 0.0
