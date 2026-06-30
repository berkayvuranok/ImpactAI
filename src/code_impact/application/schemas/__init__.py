"""Pydantic schemas for API request/response."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, HttpUrl


# ── Auth ──────────────────────────────────────────────────────────────────────

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class LoginRequest(BaseModel):
    email: str
    password: str


# ── Repository ────────────────────────────────────────────────────────────────

class CreateRepositoryRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    url: HttpUrl
    default_branch: str = "main"
    provider: str = "github"


class RepositoryResponse(BaseModel):
    id: UUID
    name: str
    url: str
    default_branch: str
    provider: str
    last_synced_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class SyncRepositoryRequest(BaseModel):
    full_sync: bool = False
    since_sha: str | None = None


class SyncJobResponse(BaseModel):
    job_id: UUID
    repository_id: UUID
    status: str
    message: str


# ── Prediction ────────────────────────────────────────────────────────────────

class PredictRequest(BaseModel):
    repository_id: UUID
    diff: str = Field(..., min_length=1)
    base_sha: str | None = None
    head_sha: str | None = None
    pull_request_id: UUID | None = None


class AffectedFileResponse(BaseModel):
    file_path: str
    break_probability: float
    node_importance: float
    rank: int
    explanation: str | None = None


class SimilarCommitResponse(BaseModel):
    commit_sha: str
    similarity_score: float
    message: str
    is_regression: bool
    linked_issue_ids: list[str] = []


class ReviewerSuggestionResponse(BaseModel):
    user_id: UUID
    username: str
    score: float
    expertise_areas: list[str]
    ownership_files: list[str]
    rationale: str | None = None


class ExplanationResponse(BaseModel):
    root_cause: str
    risk_explanation: str
    affected_files_explanation: str
    reviewer_explanation: str | None = None


class PredictionResponse(BaseModel):
    id: UUID
    repository_id: UUID
    status: str
    risk_score: float | None = None
    regression_probability: float | None = None
    confidence_score: float | None = None
    affected_files: list[AffectedFileResponse] = []
    similar_commits: list[SimilarCommitResponse] = []
    suggested_reviewers: list[ReviewerSuggestionResponse] = []
    explanation: ExplanationResponse | None = None
    error_message: str | None = None
    created_at: datetime
    completed_at: datetime | None = None


class PredictAcceptedResponse(BaseModel):
    prediction_id: UUID
    status: str = "pending"
    message: str = "Prediction job queued"


# ── Graph ─────────────────────────────────────────────────────────────────────

class GraphNodeResponse(BaseModel):
    node_id: str
    node_type: str
    name: str
    file_path: str | None
    properties: dict = {}


class GraphEdgeResponse(BaseModel):
    source_id: str
    target_id: str
    edge_type: str
    weight: float


class GraphResponse(BaseModel):
    snapshot_id: UUID
    commit_sha: str
    node_count: int
    edge_count: int
    nodes: list[GraphNodeResponse]
    edges: list[GraphEdgeResponse]


# ── Risk / History ────────────────────────────────────────────────────────────

class RiskSummaryResponse(BaseModel):
    repository_id: UUID
    average_risk_score: float
    high_risk_predictions: int
    total_predictions: int
    trend: list[dict]


class PredictionHistoryResponse(BaseModel):
    items: list[PredictionResponse]
    total: int
    limit: int
    offset: int


# ── Health ────────────────────────────────────────────────────────────────────

class HealthResponse(BaseModel):
    status: str
    version: str
    environment: str


# ── Analysis ──────────────────────────────────────────────────────────────────

class AnalyzeDiffRequest(BaseModel):
    diff: str = Field(..., min_length=1)
    file_contents_before: dict[str, str] | None = None
    file_contents_after: dict[str, str] | None = None


class FileChangeResponse(BaseModel):
    file_path: str
    change_type: str
    added_lines: int
    deleted_lines: int
    language: str | None = None
    old_path: str | None = None
    functions_added: list[str] = []
    functions_modified: list[str] = []
    functions_deleted: list[str] = []
    classes_added: list[str] = []
    classes_modified: list[str] = []
    complexity_before: float | None = None
    complexity_after: float | None = None
    complexity_delta: float = 0.0
    imports_added: list[str] = []
    imports_removed: list[str] = []


class AnalyzeDiffResponse(BaseModel):
    changed_files: list[str]
    added_lines: int
    deleted_lines: int
    modified_functions: list[str]
    renamed_files: dict[str, str]
    complexity_delta: float
    deleted_code_ratio: float
    dependency_changes: list[str]
    languages_affected: list[str]
    file_changes: list[FileChangeResponse] = []


# ── Embeddings / Search ───────────────────────────────────────────────────────

class IndexEmbeddingsResponse(BaseModel):
    repository_id: UUID
    commits_indexed: int
    commits_skipped: int
    issues_indexed: int
    issues_skipped: int


class SearchSimilarRequest(BaseModel):
    repository_id: UUID
    diff: str = Field(..., min_length=1)
    top_k_commits: int = Field(default=10, ge=1, le=50)
    top_k_bugs: int = Field(default=5, ge=1, le=50)


class SearchSimilarResponse(BaseModel):
    repository_id: UUID
    similar_commits: list[SimilarCommitResponse]
    similar_bugs: list[dict]
