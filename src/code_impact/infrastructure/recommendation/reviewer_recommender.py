"""ML-based reviewer recommender using file ownership profiles."""

from __future__ import annotations

from uuid import UUID

from code_impact.domain.entities import ReviewerProfile
from code_impact.domain.repositories import IReviewerProfileRepository
from code_impact.domain.services import IReviewerRecommender
from code_impact.domain.value_objects.risk import AffectedFilePrediction
from code_impact.domain.entities import ReviewerSuggestion


class ReviewerRecommender(IReviewerRecommender):
    """Rank reviewers by ownership overlap and expertise match."""

    def __init__(self, reviewer_repo: IReviewerProfileRepository) -> None:
        self._reviewers = reviewer_repo

    async def recommend(
        self,
        repository_id: UUID,
        affected_files: list[AffectedFilePrediction],
        top_k: int = 5,
    ) -> list[ReviewerSuggestion]:
        profiles = await self._reviewers.list_by_repository(repository_id)
        if not profiles:
            return []

        target_paths = {f.file_path for f in affected_files}
        target_dirs = {self._dir_of(p) for p in target_paths}

        scored: list[tuple[ReviewerProfile, float, list[str], str]] = []
        for profile in profiles:
            owned_files = self._owned_files(profile, target_paths, target_dirs)
            if not owned_files and not profile.expertise_area:
                continue
            overlap = self._ownership_overlap(profile, target_paths)
            expertise = self._expertise_match(profile, target_paths, target_dirs)
            base = profile.ownership_score * 0.3
            score = min(base + overlap * 0.5 + expertise * 0.2, 1.0)
            rationale = self._rationale(profile, owned_files, overlap, expertise)
            scored.append((profile, score, owned_files, rationale))

        scored.sort(key=lambda item: item[1], reverse=True)
        return [
            ReviewerSuggestion(
                user_id=profile.user_id,
                username=profile.username,
                score=round(score, 4),
                expertise_areas=[profile.expertise_area] if profile.expertise_area else [],
                ownership_files=owned_files[:5],
                rationale=rationale,
            )
            for profile, score, owned_files, rationale in scored[:top_k]
        ]

    @staticmethod
    def _dir_of(path: str) -> str:
        parts = path.rsplit("/", 1)
        return parts[0] if len(parts) > 1 else ""

    @staticmethod
    def _owned_files(
        profile: ReviewerProfile,
        target_paths: set[str],
        target_dirs: set[str],
    ) -> list[str]:
        owned: list[str] = []
        for path, weight in profile.file_ownership_map.items():
            if weight <= 0:
                continue
            if path in target_paths or ReviewerRecommender._dir_of(path) in target_dirs:
                owned.append(path)
        return owned

    @staticmethod
    def _ownership_overlap(profile: ReviewerProfile, target_paths: set[str]) -> float:
        if not target_paths or not profile.file_ownership_map:
            return 0.0
        hits = sum(
            profile.file_ownership_map.get(path, 0.0)
            for path in target_paths
            if path in profile.file_ownership_map
        )
        return min(hits / len(target_paths), 1.0)

    @staticmethod
    def _expertise_match(
        profile: ReviewerProfile,
        target_paths: set[str],
        target_dirs: set[str],
    ) -> float:
        if not profile.expertise_area:
            return 0.0
        area = profile.expertise_area.lower()
        for path in target_paths:
            if area in path.lower():
                return 1.0
        for directory in target_dirs:
            if area in directory.lower():
                return 0.7
        return 0.0

    @staticmethod
    def _rationale(
        profile: ReviewerProfile,
        owned_files: list[str],
        overlap: float,
        expertise: float,
    ) -> str:
        if owned_files:
            return f"Owns {len(owned_files)} affected file(s); overlap={overlap:.2f}"
        if expertise > 0:
            return f"Expertise match in {profile.expertise_area}"
        return f"Repository contributor (ownership={profile.ownership_score:.2f})"
