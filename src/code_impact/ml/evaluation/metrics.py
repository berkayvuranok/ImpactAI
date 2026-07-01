"""Evaluation metrics for GNN training."""

from __future__ import annotations

import math


def compute_metrics(
    predictions: list[dict[str, float]],
    labels: list[dict[str, float | list[str]]],
) -> dict[str, float]:
    if not predictions:
        return {"count": 0.0}

    n = len(predictions)
    risk_errors = [
        abs(float(p["risk_score"]) - float(labels[i]["risk_score"])) for i, p in enumerate(predictions)
    ]
    mse = sum(e * e for e in risk_errors) / n
    rmse = math.sqrt(mse)

    tp = fp = tn = fn = 0
    for i, pred in enumerate(predictions):
        p = 1 if pred.get("regression_probability", 0.0) >= 0.5 else 0
        y = 1 if float(labels[i]["is_regression"]) >= 0.5 else 0
        if p == 1 and y == 1:
            tp += 1
        elif p == 1:
            fp += 1
        elif y == 1:
            fn += 1
        else:
            tn += 1

    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0

    return {
        "count": float(n),
        "risk_rmse": rmse,
        "risk_mae": sum(risk_errors) / n,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "roc_auc_proxy": f1,
    }


def precision_at_k(
    ranked_files: list[tuple[str, float]],
    ground_truth: set[str],
    k: int = 5,
) -> float:
    if not ranked_files or not ground_truth:
        return 0.0
    top = [path for path, _ in ranked_files[:k]]
    hits = sum(1 for path in top if path in ground_truth)
    return hits / min(k, len(top))
