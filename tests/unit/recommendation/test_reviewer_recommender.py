"""Tests for reviewer recommender."""

from uuid import uuid4

import pytest

from code_impact.domain.entities import ReviewerProfile
from code_impact.domain.value_objects.risk import AffectedFilePrediction
from code_impact.infrastructure.recommendation.reviewer_recommender import ReviewerRecommender
from support.in_memory_prediction_repositories import InMemoryReviewerProfileRepository


@pytest.mark.asyncio
async def test_reviewer_recommender_ranks_by_ownership():
    repo_id = uuid4()
    user_a = uuid4()
    user_b = uuid4()
    profiles = InMemoryReviewerProfileRepository()
    await profiles.create_batch(
        [
            ReviewerProfile(
                id=uuid4(),
                user_id=user_a,
                repository_id=repo_id,
                username="alice",
                expertise_area="parser",
                ownership_score=0.8,
                file_ownership_map={"a.py": 0.9, "src/parser.py": 0.7},
            ),
            ReviewerProfile(
                id=uuid4(),
                user_id=user_b,
                repository_id=repo_id,
                username="bob",
                expertise_area="ui",
                ownership_score=0.3,
                file_ownership_map={"ui/app.tsx": 0.6},
            ),
        ]
    )

    recommender = ReviewerRecommender(profiles)
    suggestions = await recommender.recommend(
        repo_id,
        [
            AffectedFilePrediction("a.py", 0.8, 0.7, 1),
            AffectedFilePrediction("src/parser.py", 0.6, 0.5, 2),
        ],
    )
    assert suggestions
    assert suggestions[0].username == "alice"
    assert suggestions[0].score >= suggestions[-1].score
