"""Fuse GNN, classical ML, and historical search signals."""

from __future__ import annotations

from dataclasses import dataclass, field

from code_impact.domain.entities import SimilarCommit
from code_impact.domain.services import GNNPredictionResult
from code_impact.domain.value_objects.risk import (
    AffectedFilePrediction,
    ConfidenceScore,
    RegressionProbability,
    RiskScore,
)
from code_impact.ml.risk.classical_risk_classifier import ClassicalRiskResult


@dataclass(frozen=True, slots=True)
class FusedPredictionResult:
    risk_score: RiskScore
    regression_probability: RegressionProbability
    confidence_score: ConfidenceScore
    affected_files: list[AffectedFilePrediction]
    fusion_weights: dict[str, float] = field(default_factory=dict)
    component_scores: dict[str, float] = field(default_factory=dict)


class EnsembleFusionService:
    """Combine multi-model predictions with variance-based confidence."""

    def __init__(
        self,
        gnn_weight: float = 0.5,
        classical_weight: float = 0.3,
        historical_weight: float = 0.2,
    ) -> None:
        total = gnn_weight + classical_weight + historical_weight
        self._w_gnn = gnn_weight / total
        self._w_classical = classical_weight / total
        self._w_historical = historical_weight / total

    def fuse(
        self,
        gnn_result: GNNPredictionResult,
        classical_result: ClassicalRiskResult,
        similar_commits: list[SimilarCommit],
        *,
        historical_boost: float | None = None,
    ) -> FusedPredictionResult:
        hist_risk, hist_reg = self._historical_signals(similar_commits, historical_boost)

        risk_components = {
            "gnn": gnn_result.risk_score.value,
            "classical": classical_result.risk_score.value,
            "historical": hist_risk,
        }
        reg_components = {
            "gnn": gnn_result.regression_probability.value,
            "classical": classical_result.regression_probability.value,
            "historical": hist_reg,
        }

        fused_risk = (
            risk_components["gnn"] * self._w_gnn
            + risk_components["classical"] * self._w_classical
            + risk_components["historical"] * self._w_historical
        )
        fused_reg = (
            reg_components["gnn"] * self._w_gnn
            + reg_components["classical"] * self._w_classical
            + reg_components["historical"] * self._w_historical
        )

        confidence = self._confidence_from_variance(
            list(risk_components.values()),
            list(reg_components.values()),
            gnn_result.confidence_score.value,
        )
        affected = self._merge_affected_files(gnn_result.affected_files, similar_commits)

        return FusedPredictionResult(
            risk_score=RiskScore(min(max(fused_risk, 0.0), 100.0)),
            regression_probability=RegressionProbability(min(max(fused_reg, 0.0), 1.0)),
            confidence_score=ConfidenceScore(confidence),
            affected_files=affected,
            fusion_weights={
                "gnn": self._w_gnn,
                "classical": self._w_classical,
                "historical": self._w_historical,
            },
            component_scores={**risk_components, **{f"reg_{k}": v for k, v in reg_components.items()}},
        )

    @staticmethod
    def _historical_signals(
        similar_commits: list[SimilarCommit],
        historical_boost: float | None,
    ) -> tuple[float, float]:
        if not similar_commits:
            return 15.0, 0.1
        regression_rate = sum(1 for c in similar_commits if c.is_regression) / len(similar_commits)
        avg_sim = sum(c.similarity_score for c in similar_commits) / len(similar_commits)
        boost = historical_boost if historical_boost is not None else avg_sim
        risk = min(20.0 + regression_rate * 60.0 + boost * 15.0, 95.0)
        reg = min(regression_rate * 0.7 + boost * 0.25, 0.95)
        return risk, reg

    @staticmethod
    def _confidence_from_variance(
        risk_vals: list[float],
        reg_vals: list[float],
        gnn_confidence: float,
    ) -> float:
        if not risk_vals:
            return 0.5
        risk_mean = sum(risk_vals) / len(risk_vals)
        risk_var = sum((v - risk_mean) ** 2 for v in risk_vals) / len(risk_vals)
        reg_mean = sum(reg_vals) / len(reg_vals)
        reg_var = sum((v - reg_mean) ** 2 for v in reg_vals) / len(reg_vals)
        disagreement = min((risk_var / 2500.0 + reg_var) / 2.0, 1.0)
        return min(max(0.35 + gnn_confidence * 0.45 + (1.0 - disagreement) * 0.2, 0.0), 1.0)

    @staticmethod
    def _merge_affected_files(
        gnn_files: list[AffectedFilePrediction],
        similar_commits: list[SimilarCommit],
        top_k: int = 10,
    ) -> list[AffectedFilePrediction]:
        scores: dict[str, float] = {}
        importance: dict[str, float] = {}

        for item in gnn_files:
            scores[item.file_path] = max(scores.get(item.file_path, 0.0), item.break_probability)
            importance[item.file_path] = max(
                importance.get(item.file_path, 0.0), item.node_importance
            )

        if similar_commits and similar_commits[0].is_regression:
            boost = similar_commits[0].similarity_score * 0.15
            for path in list(scores.keys())[:3]:
                scores[path] = min(scores[path] + boost, 0.99)

        ranked = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)[:top_k]
        return [
            AffectedFilePrediction(
                file_path=path,
                break_probability=prob,
                node_importance=importance.get(path, 0.3),
                rank=idx + 1,
            )
            for idx, (path, prob) in enumerate(ranked)
        ]
