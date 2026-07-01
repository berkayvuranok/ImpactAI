"""Evaluation metrics for GNN training and benchmark evaluation."""

from __future__ import annotations

import math


def compute_metrics(
    predictions: list[dict[str, float]],
    labels: list[dict[str, float | list[str] | bool]],
    *,
    k: int = 5,
) -> dict[str, float]:
    if not predictions:
        return {"count": 0.0}

    n = len(predictions)
    risk_errors = [
        abs(float(p["risk_score"]) - float(labels[i]["risk_score"]))
        for i, p in enumerate(predictions)
    ]
    mse = sum(e * e for e in risk_errors) / n
    rmse = math.sqrt(mse)

    tp = fp = tn = fn = 0
    prob_pairs: list[tuple[float, int]] = []
    precisions: list[float] = []
    recalls: list[float] = []
    mrr_scores: list[float] = []

    for i, pred in enumerate(predictions):
        reg_prob = float(pred.get("regression_probability", 0.0))
        p = 1 if reg_prob >= 0.5 else 0
        y = 1 if float(labels[i]["is_regression"]) >= 0.5 else 0
        prob_pairs.append((reg_prob, y))
        if p == 1 and y == 1:
            tp += 1
        elif p == 1:
            fp += 1
        elif y == 1:
            fn += 1
        else:
            tn += 1

        ranked = pred.get("ranked_files") or []
        gt_files = set(labels[i].get("affected_files") or [])
        if ranked and gt_files:
            precisions.append(precision_at_k(ranked, gt_files, k=k))
            recalls.append(recall_at_k(ranked, gt_files, k=k))
            mrr_scores.append(mean_reciprocal_rank(ranked, gt_files))

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
        "roc_auc_proxy": _roc_auc_proxy(prob_pairs),
        "precision_at_k": sum(precisions) / len(precisions) if precisions else 0.0,
        "recall_at_k": sum(recalls) / len(recalls) if recalls else 0.0,
        "mrr": sum(mrr_scores) / len(mrr_scores) if mrr_scores else 0.0,
        "calibration_ece": calibration_ece(prob_pairs),
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


def recall_at_k(
    ranked_files: list[tuple[str, float]],
    ground_truth: set[str],
    k: int = 5,
) -> float:
    if not ranked_files or not ground_truth:
        return 0.0
    top = {path for path, _ in ranked_files[:k]}
    hits = len(top & ground_truth)
    return hits / len(ground_truth)


def mean_reciprocal_rank(
    ranked_files: list[tuple[str, float]],
    ground_truth: set[str],
) -> float:
    for rank, (path, _) in enumerate(ranked_files, start=1):
        if path in ground_truth:
            return 1.0 / rank
    return 0.0


def calibration_ece(prob_pairs: list[tuple[float, int]], n_bins: int = 10) -> float:
    if not prob_pairs:
        return 0.0
    bins: list[list[tuple[float, int]]] = [[] for _ in range(n_bins)]
    for prob, label in prob_pairs:
        idx = min(int(prob * n_bins), n_bins - 1)
        bins[idx].append((prob, label))

    ece = 0.0
    total = len(prob_pairs)
    for bucket in bins:
        if not bucket:
            continue
        avg_conf = sum(p for p, _ in bucket) / len(bucket)
        avg_acc = sum(y for _, y in bucket) / len(bucket)
        ece += (len(bucket) / total) * abs(avg_conf - avg_acc)
    return ece


def _roc_auc_proxy(prob_pairs: list[tuple[float, int]]) -> float:
    positives = [p for p, y in prob_pairs if y == 1]
    negatives = [p for p, y in prob_pairs if y == 0]
    if not positives or not negatives:
        return 0.5
    wins = sum(1 for p in positives for n in negatives if p > n)
    ties = sum(1 for p in positives for n in negatives if p == n)
    return (wins + 0.5 * ties) / (len(positives) * len(negatives))


def aggregate_metrics(per_sample: list[dict[str, float]]) -> dict[str, float]:
    if not per_sample:
        return {"count": 0.0}
    keys = {k for sample in per_sample for k in sample if k != "count"}
    result: dict[str, float] = {"count": float(len(per_sample))}
    for key in keys:
        values = [s[key] for s in per_sample if key in s]
        if key in {"risk_rmse", "risk_mae", "calibration_ece"}:
            result[key] = sum(values) / len(values)
        else:
            result[key] = sum(values) / len(values)
    return result
