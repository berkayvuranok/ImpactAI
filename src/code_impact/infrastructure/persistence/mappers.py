"""Map between ORM models and domain entities."""

from uuid import UUID

from code_impact.domain.entities import (
    Commit,
    EmbeddingRecord,
    GraphEdge,
    GraphNode,
    GraphSnapshot,
    Issue,
    MLModel,
    Prediction,
    PredictionExplanation,
    Repository,
    ReviewerProfile,
    ReviewerSuggestion,
    SimilarCommit,
    SyncJob,
    User,
)
from code_impact.domain.value_objects.enums import EdgeType, NodeType, PredictionStatus, RepositoryProvider, SyncJobStatus, UserRole
from code_impact.domain.value_objects.risk import (
    AffectedFilePrediction,
    ConfidenceScore,
    RegressionProbability,
    RiskScore,
)
from code_impact.infrastructure.persistence.models import (
    CommitModel,
    EmbeddingModel,
    GraphEdgeModel,
    GraphNodeModel,
    GraphSnapshotModel,
    IssueModel,
    MLModelModel,
    PredictionExplanationModel,
    PredictionModel,
    RepositoryModel,
    ReviewerProfileModel,
    SyncJobModel,
    UserModel,
    AffectedFilePredictionModel,
)


def user_to_domain(model: UserModel) -> User:
    return User(
        id=model.id,
        email=model.email,
        username=model.username,
        hashed_password=model.hashed_password,
        role=UserRole(model.role),
        is_active=model.is_active,
        created_at=model.created_at,
    )


def user_to_model(entity: User) -> UserModel:
    return UserModel(
        id=entity.id,
        email=entity.email,
        username=entity.username,
        hashed_password=entity.hashed_password,
        role=entity.role.value,
        is_active=entity.is_active,
        created_at=entity.created_at,
    )


def repository_to_domain(model: RepositoryModel) -> Repository:
    return Repository(
        id=model.id,
        owner_id=model.owner_id,
        name=model.name,
        url=model.url,
        default_branch=model.default_branch,
        provider=RepositoryProvider(model.provider),
        settings=model.settings or {},
        last_synced_at=model.last_synced_at,
        created_at=model.created_at,
    )


def repository_to_model(entity: Repository) -> RepositoryModel:
    return RepositoryModel(
        id=entity.id,
        owner_id=entity.owner_id,
        name=entity.name,
        url=entity.url,
        default_branch=entity.default_branch,
        provider=entity.provider.value,
        settings=entity.settings,
        last_synced_at=entity.last_synced_at,
        created_at=entity.created_at,
    )


def commit_to_domain(model: CommitModel) -> Commit:
    return Commit(
        id=model.id,
        repository_id=model.repository_id,
        sha=model.sha,
        message=model.message,
        author_email=model.author_email,
        committed_at=model.committed_at,
        is_regression=model.is_regression,
        is_rollback=model.is_rollback,
        metadata=model.metadata_ or {},
    )


def commit_to_model(entity: Commit) -> CommitModel:
    return CommitModel(
        id=entity.id,
        repository_id=entity.repository_id,
        sha=entity.sha,
        message=entity.message,
        author_email=entity.author_email,
        committed_at=entity.committed_at,
        is_regression=entity.is_regression,
        is_rollback=entity.is_rollback,
        metadata_=entity.metadata,
    )


def sync_job_to_domain(model: SyncJobModel) -> SyncJob:
    return SyncJob(
        id=model.id,
        repository_id=model.repository_id,
        status=SyncJobStatus(model.status),
        started_at=model.started_at,
        completed_at=model.completed_at,
        error_message=model.error_message,
        stats=model.stats or {},
        created_at=model.created_at,
    )


def sync_job_to_model(entity: SyncJob) -> SyncJobModel:
    return SyncJobModel(
        id=entity.id,
        repository_id=entity.repository_id,
        status=entity.status.value,
        started_at=entity.started_at,
        completed_at=entity.completed_at,
        error_message=entity.error_message,
        stats=entity.stats,
        created_at=entity.created_at,
    )


def graph_node_to_domain(model: GraphNodeModel) -> GraphNode:
    return GraphNode(
        id=model.id,
        snapshot_id=model.snapshot_id,
        node_id=model.node_id,
        node_type=NodeType(model.node_type),
        name=model.name,
        file_path=model.file_path,
        properties=model.properties or {},
    )


def graph_edge_to_domain(model: GraphEdgeModel) -> GraphEdge:
    return GraphEdge(
        id=model.id,
        snapshot_id=model.snapshot_id,
        source_id=model.source_id,
        target_id=model.target_id,
        edge_type=EdgeType(model.edge_type),
        weight=model.weight,
        properties=model.properties or {},
    )


def graph_snapshot_to_domain(
    model: GraphSnapshotModel,
    nodes: list[GraphNode] | None = None,
    edges: list[GraphEdge] | None = None,
) -> GraphSnapshot:
    return GraphSnapshot(
        id=model.id,
        repository_id=model.repository_id,
        commit_sha=model.commit_sha,
        node_count=model.node_count,
        edge_count=model.edge_count,
        storage_path=model.storage_path,
        created_at=model.created_at,
        nodes=nodes or [],
        edges=edges or [],
    )


def graph_node_to_model(entity: GraphNode) -> GraphNodeModel:
    return GraphNodeModel(
        id=entity.id,
        snapshot_id=entity.snapshot_id,
        node_id=entity.node_id,
        node_type=entity.node_type.value,
        name=entity.name,
        file_path=entity.file_path,
        properties=entity.properties,
    )


def graph_edge_to_model(entity: GraphEdge) -> GraphEdgeModel:
    return GraphEdgeModel(
        id=entity.id,
        snapshot_id=entity.snapshot_id,
        source_id=entity.source_id,
        target_id=entity.target_id,
        edge_type=entity.edge_type.value,
        weight=entity.weight,
        properties=entity.properties,
    )


def graph_snapshot_to_model(entity: GraphSnapshot) -> GraphSnapshotModel:
    return GraphSnapshotModel(
        id=entity.id,
        repository_id=entity.repository_id,
        commit_sha=entity.commit_sha,
        node_count=entity.node_count,
        edge_count=entity.edge_count,
        storage_path=entity.storage_path,
        created_at=entity.created_at,
    )


def issue_to_domain(model: IssueModel) -> Issue:
    return Issue(
        id=model.id,
        repository_id=model.repository_id,
        external_id=model.external_id,
        title=model.title,
        state=model.state,
        issue_type=model.issue_type,
        linked_commit_id=model.linked_commit_id,
        created_at=model.created_at,
    )


def issue_to_model(entity: Issue) -> IssueModel:
    return IssueModel(
        id=entity.id,
        repository_id=entity.repository_id,
        external_id=entity.external_id,
        title=entity.title,
        state=entity.state,
        issue_type=entity.issue_type,
        linked_commit_id=entity.linked_commit_id,
        created_at=entity.created_at,
    )


def embedding_to_domain(model: EmbeddingModel) -> EmbeddingRecord:
    return EmbeddingRecord(
        id=model.id,
        repository_id=model.repository_id,
        entity_type=model.entity_type,
        entity_id=model.entity_id,
        model_name=model.model_name,
        dimension=model.dimension,
        qdrant_point_id=model.qdrant_point_id,
        created_at=model.created_at,
    )


def embedding_to_model(entity: EmbeddingRecord) -> EmbeddingModel:
    return EmbeddingModel(
        id=entity.id,
        repository_id=entity.repository_id,
        entity_type=entity.entity_type,
        entity_id=entity.entity_id,
        model_name=entity.model_name,
        dimension=entity.dimension,
        qdrant_point_id=entity.qdrant_point_id,
        created_at=entity.created_at,
    )


def ml_model_to_domain(model: MLModelModel) -> MLModel:
    return MLModel(
        id=model.id,
        name=model.name,
        version=model.version,
        model_type=model.model_type,
        artifact_path=model.artifact_path,
        metrics=model.metrics or {},
        is_active=model.is_active,
        trained_at=model.trained_at,
    )


def ml_model_to_model(entity: MLModel) -> MLModelModel:
    return MLModelModel(
        id=entity.id,
        name=entity.name,
        version=entity.version,
        model_type=entity.model_type,
        artifact_path=entity.artifact_path,
        metrics=entity.metrics,
        is_active=entity.is_active,
        trained_at=entity.trained_at,
    )


def prediction_to_domain(model: PredictionModel) -> Prediction:
    output = model.output_payload or {}
    similar = [
        SimilarCommit(
            commit_sha=item.get("commit_sha", ""),
            similarity_score=float(item.get("similarity_score", 0.0)),
            message=item.get("message", ""),
            is_regression=bool(item.get("is_regression", False)),
            linked_issue_ids=item.get("linked_issue_ids", []),
        )
        for item in output.get("similar_commits", [])
    ]
    reviewers = [
        ReviewerSuggestion(
            user_id=UUID(str(item["user_id"])),
            username=item.get("username", ""),
            score=float(item.get("score", 0.0)),
            expertise_areas=item.get("expertise_areas", []),
            ownership_files=item.get("ownership_files", []),
            rationale=item.get("rationale"),
        )
        for item in output.get("suggested_reviewers", [])
    ]
    explanation = None
    if model.explanation:
        explanation = PredictionExplanation(
            root_cause=model.explanation.root_cause,
            risk_explanation=model.explanation.risk_explanation,
            affected_files_explanation=model.explanation.affected_files_explanation,
            reviewer_explanation=model.explanation.reviewer_explanation,
            attention_summary=model.explanation.attention_summary or {},
        )
    return Prediction(
        id=model.id,
        repository_id=model.repository_id,
        created_by=model.created_by,
        status=PredictionStatus(model.status),
        input_payload=model.input_payload or {},
        pull_request_id=model.pull_request_id,
        model_id=model.model_id,
        risk_score=RiskScore(model.risk_score) if model.risk_score is not None else None,
        regression_probability=(
            RegressionProbability(model.regression_probability)
            if model.regression_probability is not None
            else None
        ),
        confidence_score=(
            ConfidenceScore(model.confidence_score) if model.confidence_score is not None else None
        ),
        affected_files=[
            AffectedFilePrediction(
                file_path=f.file_path,
                break_probability=f.break_probability,
                node_importance=f.node_importance,
                rank=f.rank,
                explanation=f.explanation,
            )
            for f in model.affected_files
        ],
        similar_commits=similar,
        suggested_reviewers=reviewers,
        explanation=explanation,
        output_payload=output,
        error_message=model.error_message,
        created_at=model.created_at,
        completed_at=model.completed_at,
    )


def prediction_to_model(entity: Prediction) -> PredictionModel:
    output = dict(entity.output_payload)
    output["similar_commits"] = [
        {
            "commit_sha": c.commit_sha,
            "similarity_score": c.similarity_score,
            "message": c.message,
            "is_regression": c.is_regression,
            "linked_issue_ids": c.linked_issue_ids,
        }
        for c in entity.similar_commits
    ]
    output["suggested_reviewers"] = [
        {
            "user_id": str(r.user_id),
            "username": r.username,
            "score": r.score,
            "expertise_areas": r.expertise_areas,
            "ownership_files": r.ownership_files,
            "rationale": r.rationale,
        }
        for r in entity.suggested_reviewers
    ]
    return PredictionModel(
        id=entity.id,
        repository_id=entity.repository_id,
        pull_request_id=entity.pull_request_id,
        created_by=entity.created_by,
        model_id=entity.model_id,
        status=entity.status.value,
        risk_score=entity.risk_score.value if entity.risk_score else None,
        regression_probability=(
            entity.regression_probability.value if entity.regression_probability else None
        ),
        confidence_score=entity.confidence_score.value if entity.confidence_score else None,
        input_payload=entity.input_payload,
        output_payload=output,
        error_message=entity.error_message,
        created_at=entity.created_at,
        completed_at=entity.completed_at,
    )


def reviewer_profile_to_domain(model: ReviewerProfileModel, username: str = "") -> ReviewerProfile:
    return ReviewerProfile(
        id=model.id,
        user_id=model.user_id,
        repository_id=model.repository_id,
        username=username,
        expertise_area=model.expertise_area,
        ownership_score=model.ownership_score,
        file_ownership_map=model.file_ownership_map or {},
    )
