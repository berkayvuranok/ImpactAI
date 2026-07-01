"""Deterministic template explanations for tests and fallback."""

from __future__ import annotations

from code_impact.domain.entities import PredictionExplanation
from code_impact.domain.services import ExplanationContext, IExplanationGenerator


class TemplateExplanationGenerator(IExplanationGenerator):
    """Rich narrative from ML outputs — no external LLM call."""

    async def generate(self, context: ExplanationContext) -> PredictionExplanation:
        diff = context.diff_result
        risk = context.fused_risk_score.value
        reg = context.fused_regression_probability.value
        conf = context.fused_confidence_score.value

        file_list = ", ".join(f.file_path for f in context.affected_files[:5]) or "none flagged"
        fn_list = ", ".join(diff.modified_functions[:5]) or "none detected"

        regression_commits = [c for c in context.similar_commits if c.is_regression]
        hist_note = (
            f"{len(regression_commits)} similar past commit(s) led to regressions"
            if regression_commits
            else "no strongly similar regression commits found"
        )

        root_cause = (
            f"The change touches {len(diff.changed_files)} file(s) "
            f"(+{diff.added_lines}/-{diff.deleted_lines} lines) "
            f"with complexity delta {diff.complexity_delta:+.1f}. "
            f"Modified symbols include: {fn_list}."
        )

        risk_explanation = (
            f"Ensemble risk score is {risk:.1f}/100 with regression probability {reg:.0%} "
            f"and confidence {conf:.0%}. "
            f"GNN contributed {context.gnn_result.risk_score.value:.1f}, "
            f"historical signal: {hist_note}."
        )

        affected_files_explanation = (
            f"Top affected files by break probability: {file_list}. "
            f"These are ranked by GNN node scores fused with graph proximity to changed files."
        )

        if context.suggested_reviewers:
            names = ", ".join(r.username for r in context.suggested_reviewers[:3])
            reviewer_explanation = (
                f"Suggested reviewers ({names}) have the highest ownership overlap "
                f"with affected paths and matching expertise areas."
            )
        else:
            reviewer_explanation = "No reviewer profiles are configured for this repository."

        return PredictionExplanation(
            root_cause=root_cause,
            risk_explanation=risk_explanation,
            affected_files_explanation=affected_files_explanation,
            reviewer_explanation=reviewer_explanation,
            attention_summary={
                "generator": "template",
                "fusion_metadata": context.fusion_metadata,
                "similar_bug_count": len(context.similar_bugs),
            },
        )
