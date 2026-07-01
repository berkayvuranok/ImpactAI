"""Domain service interfaces for ML and analysis pipelines."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from uuid import UUID

from code_impact.domain.entities import (
    GraphSnapshot,
    PredictionExplanation,
    ReviewerSuggestion,
    SimilarCommit,
)
from code_impact.domain.value_objects.risk import (
    AffectedFilePrediction,
    ConfidenceScore,
    RegressionProbability,
    RiskScore,
)


@dataclass
class DiffAnalysisResult:
    changed_files: list[str]
    added_lines: int
    deleted_lines: int
    modified_functions: list[str]
    renamed_files: dict[str, str]
    complexity_delta: float
    deleted_code_ratio: float
    raw_diff: str


@dataclass
class GNNPredictionResult:
    risk_score: RiskScore
    regression_probability: RegressionProbability
    confidence_score: ConfidenceScore
    affected_files: list[AffectedFilePrediction]
    node_importance: dict[str, float]
    edge_importance: list[tuple[str, str, float]]


@dataclass
class ExplanationContext:
    """All ML outputs passed to the explanation layer — LLM must not alter these."""

    diff_result: DiffAnalysisResult
    gnn_result: GNNPredictionResult
    fused_risk_score: RiskScore
    fused_regression_probability: RegressionProbability
    fused_confidence_score: ConfidenceScore
    affected_files: list[AffectedFilePrediction]
    similar_commits: list[SimilarCommit]
    similar_bugs: list[dict] = field(default_factory=list)
    suggested_reviewers: list[ReviewerSuggestion] = field(default_factory=list)
    fusion_metadata: dict = field(default_factory=dict)


class IDiffParser(ABC):
    @abstractmethod
    async def parse(self, diff: str) -> DiffAnalysisResult: ...


class IGraphBuilder(ABC):
    @abstractmethod
    async def build_from_repository(
        self, repository_id: UUID, commit_sha: str
    ) -> GraphSnapshot: ...

    @abstractmethod
    async def apply_diff_delta(
        self, snapshot: GraphSnapshot, diff_result: DiffAnalysisResult
    ) -> GraphSnapshot: ...


class IEmbeddingService(ABC):
    @abstractmethod
    async def embed_text(self, text: str) -> list[float]: ...

    @abstractmethod
    async def embed_code(self, code: str, language: str) -> list[float]: ...

    @abstractmethod
    async def embed_batch(self, texts: list[str]) -> list[list[float]]: ...

    @property
    @abstractmethod
    def model_name(self) -> str: ...

    @property
    @abstractmethod
    def dimension(self) -> int: ...


class IGNNPredictor(ABC):
    """GNN-based prediction — NOT LLM."""

    @abstractmethod
    async def predict(
        self,
        graph_snapshot: GraphSnapshot,
        diff_result: DiffAnalysisResult,
        historical_embedding: list[float] | None = None,
    ) -> GNNPredictionResult: ...


class IHistoricalSearch(ABC):
    @abstractmethod
    async def find_similar_commits(
        self,
        repository_id: UUID,
        diff_embedding: list[float],
        top_k: int = 10,
    ) -> list[SimilarCommit]: ...

    @abstractmethod
    async def find_similar_bugs(
        self,
        repository_id: UUID,
        diff_embedding: list[float],
        top_k: int = 5,
    ) -> list[dict]: ...


class IReviewerRecommender(ABC):
    @abstractmethod
    async def recommend(
        self,
        repository_id: UUID,
        affected_files: list[AffectedFilePrediction],
        top_k: int = 5,
    ) -> list[ReviewerSuggestion]: ...


class IExplanationGenerator(ABC):
    """LLM-based explanation — NOT prediction."""

    @abstractmethod
    async def generate(self, context: ExplanationContext) -> PredictionExplanation: ...
