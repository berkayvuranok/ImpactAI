"""Tests for template explanation generator."""

import pytest

from code_impact.domain.services import ExplanationContext
from code_impact.infrastructure.llm.prompt_builder import SYSTEM_PROMPT, build_explanation_prompt
from code_impact.infrastructure.llm.template_explanation_generator import TemplateExplanationGenerator
from code_impact.ml.inference.mock_gnn_predictor import MockGNNPredictor
from support.ml_fixtures import sample_diff, sample_graph


@pytest.mark.asyncio
async def test_template_explanation_generator():
    gnn = await MockGNNPredictor().predict(sample_graph(), sample_diff())
    context = ExplanationContext(
        diff_result=sample_diff(),
        gnn_result=gnn,
        fused_risk_score=gnn.risk_score,
        fused_regression_probability=gnn.regression_probability,
        fused_confidence_score=gnn.confidence_score,
        affected_files=gnn.affected_files,
        similar_commits=[],
        similar_bugs=[],
        suggested_reviewers=[],
        fusion_metadata={"fusion_weights": {"gnn": 0.5}},
    )
    explanation = await TemplateExplanationGenerator().generate(context)
    assert explanation.root_cause
    assert explanation.risk_explanation
    assert explanation.affected_files_explanation
    assert explanation.attention_summary.get("generator") == "template"


def test_prompt_builder_includes_ml_scores():
    from code_impact.domain.value_objects.risk import (
        ConfidenceScore,
        RegressionProbability,
        RiskScore,
    )
    from code_impact.domain.services import GNNPredictionResult

    gnn = GNNPredictionResult(
        risk_score=RiskScore(42.0),
        regression_probability=RegressionProbability(0.3),
        confidence_score=ConfidenceScore(0.6),
        affected_files=[],
        node_importance={},
        edge_importance=[],
    )
    context = ExplanationContext(
        diff_result=sample_diff(),
        gnn_result=gnn,
        fused_risk_score=RiskScore(50.0),
        fused_regression_probability=RegressionProbability(0.4),
        fused_confidence_score=ConfidenceScore(0.7),
        affected_files=[],
        similar_commits=[],
    )
    prompt = build_explanation_prompt(context)
    assert "50.0" in prompt
    assert "DO NOT" in SYSTEM_PROMPT or "MUST NOT" in SYSTEM_PROMPT
