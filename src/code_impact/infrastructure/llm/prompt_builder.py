"""Build structured prompts for LLM explanation — never for prediction."""

from __future__ import annotations

import json

from code_impact.domain.services import ExplanationContext

SYSTEM_PROMPT = """You are a senior software engineer explaining code change impact.
You MUST NOT predict or modify risk scores, probabilities, or affected file rankings.
Those values are already computed by ML models (GNN + classical ML ensemble).
Your job is to explain WHY the ML system produced these results in clear prose.
Respond with valid JSON only, no markdown fences, using this schema:
{
  "root_cause": "string — likely underlying reason for the change impact",
  "risk_explanation": "string — explain the given risk score and regression probability",
  "affected_files_explanation": "string — explain why listed files may break",
  "reviewer_explanation": "string — justify suggested reviewers or note if none"
}
"""


def build_explanation_prompt(context: ExplanationContext) -> str:
    top_files = [
        {
            "path": f.file_path,
            "break_probability": round(f.break_probability, 3),
            "rank": f.rank,
        }
        for f in context.affected_files[:8]
    ]
    similar = [
        {
            "sha": c.commit_sha[:8],
            "similarity": round(c.similarity_score, 3),
            "is_regression": c.is_regression,
            "message": c.message[:120],
        }
        for c in context.similar_commits[:5]
    ]
    reviewers = [
        {
            "username": r.username,
            "score": round(r.score, 3),
            "ownership_files": r.ownership_files[:3],
            "rationale": r.rationale,
        }
        for r in context.suggested_reviewers[:5]
    ]
    payload = {
        "instruction": "Explain the ML prediction results below. Do NOT invent new scores.",
        "ml_predictions": {
            "risk_score": round(context.fused_risk_score.value, 1),
            "regression_probability": round(context.fused_regression_probability.value, 3),
            "confidence_score": round(context.fused_confidence_score.value, 3),
            "gnn_risk_score": round(context.gnn_result.risk_score.value, 1),
            "gnn_regression_probability": round(context.gnn_result.regression_probability.value, 3),
        },
        "diff_summary": {
            "changed_files": context.diff_result.changed_files[:15],
            "added_lines": context.diff_result.added_lines,
            "deleted_lines": context.diff_result.deleted_lines,
            "modified_functions": context.diff_result.modified_functions[:10],
            "complexity_delta": round(context.diff_result.complexity_delta, 2),
        },
        "affected_files": top_files,
        "similar_commits": similar,
        "similar_bugs": context.similar_bugs[:3],
        "suggested_reviewers": reviewers,
        "fusion_metadata": context.fusion_metadata,
    }
    return json.dumps(payload, indent=2)
