"""Heuristic / classical risk classifier — not LLM."""

from __future__ import annotations

from dataclasses import dataclass

from code_impact.domain.entities import SimilarCommit
from code_impact.domain.services import DiffAnalysisResult
from code_impact.domain.value_objects.risk import RegressionProbability, RiskScore
from code_impact.ml.risk.feature_extractor import DiffRiskFeatures, extract_risk_features


@dataclass(frozen=True, slots=True)
class ClassicalRiskResult:
    risk_score: RiskScore
    regression_probability: RegressionProbability
    features: DiffRiskFeatures


class ClassicalRiskClassifier:
    """Weighted logistic-style classifier using diff + historical features."""

    WEIGHTS: dict[str, float] = {
        "changed_file_count": 12.0,
        "added_lines_norm": 8.0,
        "deleted_lines_norm": 10.0,
        "complexity_delta_norm": 14.0,
        "deleted_code_ratio": 11.0,
        "modified_function_count": 9.0,
        "rename_count": 6.0,
        "similar_regression_rate": 18.0,
        "max_similarity": 7.0,
        "api_db_mq_surface": 13.0,
    }
    BIAS: float = 8.0

    def predict(
        self,
        diff_result: DiffAnalysisResult,
        similar_commits: list[SimilarCommit] | None = None,
        *,
        api_db_mq_hits: int = 0,
    ) -> ClassicalRiskResult:
        features = extract_risk_features(diff_result, similar_commits, api_db_mq_hits=api_db_mq_hits)
        logit = self.BIAS + sum(
            getattr(features, name) * weight for name, weight in self.WEIGHTS.items()
        )
        regression_prob = self._sigmoid((logit - 50.0) / 12.0)
        risk = min(max(logit * 0.85 + regression_prob * 20.0, 0.0), 100.0)
        return ClassicalRiskResult(
            risk_score=RiskScore(risk),
            regression_probability=RegressionProbability(regression_prob),
            features=features,
        )

    @staticmethod
    def _sigmoid(x: float) -> float:
        if x >= 0:
            z = pow(2.718281828, -x)
            return 1.0 / (1.0 + z)
        z = pow(2.718281828, x)
        return z / (1.0 + z)
