"""Tests for label extraction heuristics."""

from datetime import UTC, datetime, timedelta

from support.ml_fixtures import sample_commit, sample_diff

from code_impact.ml.training.label_extractor import LabelExtractor


def test_rollback_detection():
    extractor = LabelExtractor()
    commit = sample_commit()
    commit.message = "Revert \"bad change\""
    assert extractor.is_rollback(commit) is True


def test_regression_via_fix_commit():
    extractor = LabelExtractor()
    target = sample_commit(is_regression=False)
    target.sha = "abc12345" + "0" * 32
    fix = sample_commit(is_regression=True)
    fix.committed_at = target.committed_at + timedelta(days=2)
    fix.message = "Fix regression from abc12345"
    labels = extractor.extract_labels(target, [fix], sample_diff())
    assert labels.is_regression == 1.0
    assert labels.risk_score > 0
