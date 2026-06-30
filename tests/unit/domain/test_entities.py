"""Tests for domain entities."""

from uuid import uuid4

from code_impact.domain.entities import Prediction
from code_impact.domain.value_objects.enums import PredictionStatus
from code_impact.domain.value_objects.risk import (
    AffectedFilePrediction,
    ConfidenceScore,
    RegressionProbability,
    RiskScore,
)
from code_impact.domain.entities import PredictionExplanation, ReviewerSuggestion, SimilarCommit


class TestPrediction:
    def test_create_pending(self):
        repo_id = uuid4()
        user_id = uuid4()
        prediction = Prediction.create_pending(
            repository_id=repo_id,
            created_by=user_id,
            input_payload={"diff": "..."},
        )
        assert prediction.status == PredictionStatus.PENDING
        assert prediction.repository_id == repo_id
        assert prediction.risk_score is None

    def test_mark_completed(self):
        prediction = Prediction.create_pending(
            repository_id=uuid4(),
            created_by=uuid4(),
            input_payload={"diff": "..."},
        )
        prediction.mark_completed(
            risk_score=RiskScore(65.0),
            regression_probability=RegressionProbability(0.7),
            confidence_score=ConfidenceScore(0.85),
            affected_files=[
                AffectedFilePrediction("src/a.py", 0.9, 0.8, 1),
            ],
            similar_commits=[
                SimilarCommit("abc123", 0.92, "fix regression", True),
            ],
            suggested_reviewers=[
                ReviewerSuggestion(uuid4(), "alice", 0.95, ["backend"], ["src/a.py"]),
            ],
            explanation=PredictionExplanation(
                root_cause="Changed shared utility",
                risk_explanation="High coupling detected",
                affected_files_explanation="3 downstream files depend on changed module",
            ),
            output_payload={"model_version": "0.1.0"},
        )
        assert prediction.status == PredictionStatus.COMPLETED
        assert prediction.risk_score is not None
        assert prediction.risk_score.value == 65.0
        assert prediction.completed_at is not None

    def test_mark_failed(self):
        prediction = Prediction.create_pending(
            repository_id=uuid4(),
            created_by=uuid4(),
            input_payload={"diff": "..."},
        )
        prediction.mark_failed("Graph build timeout")
        assert prediction.status == PredictionStatus.FAILED
        assert prediction.error_message == "Graph build timeout"
