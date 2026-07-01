"""Domain entities — core business objects."""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID, uuid4

from code_impact.domain.value_objects.enums import (
    EdgeType,
    NodeType,
    PredictionStatus,
    RepositoryProvider,
    SyncJobStatus,
    UserRole,
)
from code_impact.domain.value_objects.risk import (
    AffectedFilePrediction,
    ConfidenceScore,
    RegressionProbability,
    RiskScore,
)


@dataclass
class User:
    id: UUID
    email: str
    username: str
    hashed_password: str
    role: UserRole
    is_active: bool = True
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class Repository:
    id: UUID
    owner_id: UUID
    name: str
    url: str
    default_branch: str
    provider: RepositoryProvider
    settings: dict = field(default_factory=dict)
    last_synced_at: datetime | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class SyncJob:
    id: UUID
    repository_id: UUID
    status: SyncJobStatus
    started_at: datetime | None = None
    completed_at: datetime | None = None
    error_message: str | None = None
    stats: dict = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    @classmethod
    def create(cls, repository_id: UUID) -> "SyncJob":
        return cls(
            id=uuid4(),
            repository_id=repository_id,
            status=SyncJobStatus.QUEUED,
        )

    def mark_running(self) -> None:
        self.status = SyncJobStatus.RUNNING
        self.started_at = datetime.now(UTC)

    def mark_completed(self, stats: dict) -> None:
        self.status = SyncJobStatus.COMPLETED
        self.stats = stats
        self.completed_at = datetime.now(UTC)

    def mark_failed(self, error_message: str) -> None:
        self.status = SyncJobStatus.FAILED
        self.error_message = error_message
        self.completed_at = datetime.now(UTC)


@dataclass
class Commit:
    id: UUID
    repository_id: UUID
    sha: str
    message: str
    author_email: str
    committed_at: datetime
    is_regression: bool = False
    is_rollback: bool = False
    metadata: dict = field(default_factory=dict)


@dataclass
class Issue:
    id: UUID
    repository_id: UUID
    external_id: str
    title: str
    state: str
    issue_type: str
    linked_commit_id: UUID | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class MLModel:
    id: UUID
    name: str
    version: str
    model_type: str
    artifact_path: str
    metrics: dict = field(default_factory=dict)
    is_active: bool = False
    trained_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class EmbeddingRecord:
    id: UUID
    repository_id: UUID
    entity_type: str
    entity_id: UUID
    model_name: str
    dimension: int
    qdrant_point_id: str
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class PullRequest:
    id: UUID
    repository_id: UUID
    pr_number: int
    title: str
    state: str
    head_sha: str
    base_sha: str
    diff_stats: dict = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    merged_at: datetime | None = None


@dataclass
class GraphNode:
    id: UUID
    snapshot_id: UUID
    node_id: str
    node_type: NodeType
    name: str
    file_path: str | None
    properties: dict = field(default_factory=dict)


@dataclass
class GraphEdge:
    id: UUID
    snapshot_id: UUID
    source_id: str
    target_id: str
    edge_type: EdgeType
    weight: float = 1.0
    properties: dict = field(default_factory=dict)


@dataclass
class GraphSnapshot:
    id: UUID
    repository_id: UUID
    commit_sha: str
    node_count: int
    edge_count: int
    storage_path: str
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    nodes: list[GraphNode] = field(default_factory=list)
    edges: list[GraphEdge] = field(default_factory=list)


@dataclass
class SimilarCommit:
    commit_sha: str
    similarity_score: float
    message: str
    is_regression: bool
    linked_issue_ids: list[str] = field(default_factory=list)


@dataclass
class ReviewerSuggestion:
    user_id: UUID
    username: str
    score: float
    expertise_areas: list[str]
    ownership_files: list[str]
    rationale: str | None = None


@dataclass
class PredictionExplanation:
    root_cause: str
    risk_explanation: str
    affected_files_explanation: str
    reviewer_explanation: str | None = None
    attention_summary: dict = field(default_factory=dict)


@dataclass
class Prediction:
    """Aggregate root for impact predictions."""

    id: UUID
    repository_id: UUID
    created_by: UUID
    status: PredictionStatus
    input_payload: dict
    pull_request_id: UUID | None = None
    model_id: UUID | None = None
    risk_score: RiskScore | None = None
    regression_probability: RegressionProbability | None = None
    confidence_score: ConfidenceScore | None = None
    affected_files: list[AffectedFilePrediction] = field(default_factory=list)
    similar_commits: list[SimilarCommit] = field(default_factory=list)
    suggested_reviewers: list[ReviewerSuggestion] = field(default_factory=list)
    explanation: PredictionExplanation | None = None
    output_payload: dict = field(default_factory=dict)
    error_message: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    completed_at: datetime | None = None

    @classmethod
    def create_pending(
        cls,
        repository_id: UUID,
        created_by: UUID,
        input_payload: dict,
        pull_request_id: UUID | None = None,
    ) -> "Prediction":
        return cls(
            id=uuid4(),
            repository_id=repository_id,
            created_by=created_by,
            pull_request_id=pull_request_id,
            status=PredictionStatus.PENDING,
            input_payload=input_payload,
        )

    def mark_processing(self) -> None:
        self.status = PredictionStatus.PROCESSING

    def mark_completed(
        self,
        risk_score: RiskScore,
        regression_probability: RegressionProbability,
        confidence_score: ConfidenceScore,
        affected_files: list[AffectedFilePrediction],
        similar_commits: list[SimilarCommit],
        suggested_reviewers: list[ReviewerSuggestion],
        explanation: PredictionExplanation,
        output_payload: dict,
    ) -> None:
        self.status = PredictionStatus.COMPLETED
        self.risk_score = risk_score
        self.regression_probability = regression_probability
        self.confidence_score = confidence_score
        self.affected_files = affected_files
        self.similar_commits = similar_commits
        self.suggested_reviewers = suggested_reviewers
        self.explanation = explanation
        self.output_payload = output_payload
        self.completed_at = datetime.now(UTC)

    def mark_failed(self, error_message: str) -> None:
        self.status = PredictionStatus.FAILED
        self.error_message = error_message
        self.completed_at = datetime.now(UTC)
