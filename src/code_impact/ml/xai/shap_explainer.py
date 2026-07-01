"""SHAP-style attributions for the classical risk classifier."""

from __future__ import annotations

from code_impact.ml.risk.classical_risk_classifier import ClassicalRiskClassifier
from code_impact.ml.risk.feature_extractor import DiffRiskFeatures
from code_impact.ml.xai.types import FeatureAttribution

FEATURE_LABELS: dict[str, str] = {
    "changed_file_count": "Changed files",
    "added_lines_norm": "Lines added",
    "deleted_lines_norm": "Lines deleted",
    "complexity_delta_norm": "Complexity delta",
    "deleted_code_ratio": "Deleted code ratio",
    "modified_function_count": "Modified functions",
    "rename_count": "Renamed files",
    "similar_regression_rate": "Similar regressions",
    "max_similarity": "Max commit similarity",
    "api_db_mq_surface": "API/DB/MQ surface",
}


def explain_classical_features(
    features: DiffRiskFeatures,
    classifier: ClassicalRiskClassifier | None = None,
) -> tuple[float, float, list[FeatureAttribution]]:
    """Exact linear SHAP for the weighted logit of ClassicalRiskClassifier."""
    clf = classifier or ClassicalRiskClassifier()
    feature_map = {
        name: float(getattr(features, name)) for name in clf.WEIGHTS
    }

    base_logit = clf.BIAS
    contributions = {
        name: weight * feature_map[name] for name, weight in clf.WEIGHTS.items()
    }
    output_logit = base_logit + sum(contributions.values())

    attributions = [
        FeatureAttribution(
            feature=name,
            label=FEATURE_LABELS.get(name, name),
            value=feature_map[name],
            shap_value=contrib,
        )
        for name, contrib in sorted(contributions.items(), key=lambda x: abs(x[1]), reverse=True)
    ]
    return base_logit, output_logit, attributions


def explain_classical_with_shap_library(
    features: DiffRiskFeatures,
    classifier: ClassicalRiskClassifier | None = None,
) -> tuple[float, float, list[FeatureAttribution], str]:
    """Optional SHAP library path when installed (validates linear attributions)."""
    try:
        import numpy as np
        import shap
    except ImportError:
        base, out, attrs = explain_classical_features(features, classifier)
        return base, out, attrs, "linear_exact"

    clf = classifier or ClassicalRiskClassifier()
    names = list(clf.WEIGHTS.keys())
    x = np.array([[float(getattr(features, n)) for n in names]])
    weights = np.array([clf.WEIGHTS[n] for n in names])

    explainer = shap.explainers.Linear(model=(weights, clf.BIAS), masker=x)
    shap_values = explainer(x)
    values = shap_values.values[0].tolist()
    base = float(shap_values.base_values[0])
    out = base + sum(values)

    attributions = [
        FeatureAttribution(
            feature=name,
            label=FEATURE_LABELS.get(name, name),
            value=float(getattr(features, name)),
            shap_value=float(val),
        )
        for name, val in sorted(zip(names, values, strict=True), key=lambda p: abs(p[1]), reverse=True)
    ]
    return base, out, attributions, "shap_linear"
