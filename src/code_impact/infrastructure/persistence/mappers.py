"""Map between ORM models and domain entities."""

from code_impact.domain.entities import Commit, EmbeddingRecord, GraphEdge, GraphNode, GraphSnapshot, Issue, Repository, SyncJob, User
from code_impact.domain.value_objects.enums import EdgeType, NodeType, RepositoryProvider, SyncJobStatus, UserRole
from code_impact.infrastructure.persistence.models import (
    CommitModel,
    EmbeddingModel,
    GraphEdgeModel,
    GraphNodeModel,
    GraphSnapshotModel,
    IssueModel,
    RepositoryModel,
    SyncJobModel,
    UserModel,
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
