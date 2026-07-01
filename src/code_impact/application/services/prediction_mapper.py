"""Map domain prediction entities to API schemas."""

from code_impact.application.schemas import (
    AffectedFileResponse,
    ExplanationResponse,
    PredictionResponse,
    ReviewerSuggestionResponse,
    SimilarCommitResponse,
)
from code_impact.domain.entities import Prediction


def prediction_to_response(prediction: Prediction) -> PredictionResponse:
    return PredictionResponse(
        id=prediction.id,
        repository_id=prediction.repository_id,
        status=prediction.status.value,
        risk_score=prediction.risk_score.value if prediction.risk_score else None,
        regression_probability=(
            prediction.regression_probability.value if prediction.regression_probability else None
        ),
        confidence_score=(
            prediction.confidence_score.value if prediction.confidence_score else None
        ),
        affected_files=[
            AffectedFileResponse(
                file_path=f.file_path,
                break_probability=f.break_probability,
                node_importance=f.node_importance,
                rank=f.rank,
                explanation=f.explanation,
            )
            for f in prediction.affected_files
        ],
        similar_commits=[
            SimilarCommitResponse(
                commit_sha=c.commit_sha,
                similarity_score=c.similarity_score,
                message=c.message,
                is_regression=c.is_regression,
                linked_issue_ids=c.linked_issue_ids,
            )
            for c in prediction.similar_commits
        ],
        suggested_reviewers=[
            ReviewerSuggestionResponse(
                user_id=r.user_id,
                username=r.username,
                score=r.score,
                expertise_areas=r.expertise_areas,
                ownership_files=r.ownership_files,
                rationale=r.rationale,
            )
            for r in prediction.suggested_reviewers
        ],
        explanation=(
            ExplanationResponse(
                root_cause=prediction.explanation.root_cause,
                risk_explanation=prediction.explanation.risk_explanation,
                affected_files_explanation=prediction.explanation.affected_files_explanation,
                reviewer_explanation=prediction.explanation.reviewer_explanation,
            )
            if prediction.explanation
            else None
        ),
        error_message=prediction.error_message,
        created_at=prediction.created_at,
        completed_at=prediction.completed_at,
    )
