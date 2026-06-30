"""Initial schema — all core tables.

Revision ID: 001
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(255), unique=True, nullable=False),
        sa.Column("username", sa.String(100), unique=True, nullable=False),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("role", sa.String(50), nullable=False, server_default="viewer"),
        sa.Column("is_active", sa.Boolean(), server_default="true"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()")),
    )
    op.create_index("ix_users_email", "users", ["email"])

    op.create_table(
        "repositories",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("owner_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id")),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("url", sa.String(512), unique=True, nullable=False),
        sa.Column("default_branch", sa.String(100), server_default="main"),
        sa.Column("provider", sa.String(50), server_default="github"),
        sa.Column("settings", postgresql.JSONB(), server_default="{}"),
        sa.Column("last_synced_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()")),
    )

    op.create_table(
        "ml_models",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("version", sa.String(50), nullable=False),
        sa.Column("model_type", sa.String(50), nullable=False),
        sa.Column("artifact_path", sa.String(1024), nullable=False),
        sa.Column("metrics", postgresql.JSONB(), server_default="{}"),
        sa.Column("is_active", sa.Boolean(), server_default="false"),
        sa.Column("trained_at", sa.DateTime(), server_default=sa.text("now()")),
    )

    op.create_table(
        "commits",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("repository_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("repositories.id")),
        sa.Column("sha", sa.String(40), nullable=False),
        sa.Column("message", sa.Text(), server_default=""),
        sa.Column("author_email", sa.String(255), server_default=""),
        sa.Column("committed_at", sa.DateTime(), nullable=False),
        sa.Column("is_regression", sa.Boolean(), server_default="false"),
        sa.Column("is_rollback", sa.Boolean(), server_default="false"),
        sa.Column("metadata", postgresql.JSONB(), server_default="{}"),
        sa.UniqueConstraint("repository_id", "sha", name="uq_repo_sha"),
    )
    op.create_index("ix_commits_repository_id", "commits", ["repository_id"])

    op.create_table(
        "pull_requests",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("repository_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("repositories.id")),
        sa.Column("pr_number", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(512), server_default=""),
        sa.Column("state", sa.String(50), server_default="open"),
        sa.Column("head_sha", sa.String(40), nullable=False),
        sa.Column("base_sha", sa.String(40), nullable=False),
        sa.Column("diff_stats", postgresql.JSONB(), server_default="{}"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()")),
        sa.Column("merged_at", sa.DateTime(), nullable=True),
        sa.UniqueConstraint("repository_id", "pr_number", name="uq_repo_pr"),
    )

    op.create_table(
        "predictions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("repository_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("repositories.id")),
        sa.Column("pull_request_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("pull_requests.id"), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id")),
        sa.Column("model_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("ml_models.id"), nullable=True),
        sa.Column("status", sa.String(50), server_default="pending"),
        sa.Column("risk_score", sa.Float(), nullable=True),
        sa.Column("regression_probability", sa.Float(), nullable=True),
        sa.Column("confidence_score", sa.Float(), nullable=True),
        sa.Column("input_payload", postgresql.JSONB(), server_default="{}"),
        sa.Column("output_payload", postgresql.JSONB(), server_default="{}"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()")),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_predictions_repository_id", "predictions", ["repository_id"])
    op.create_index("ix_predictions_status", "predictions", ["status"])

    op.create_table(
        "affected_file_predictions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("prediction_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("predictions.id")),
        sa.Column("file_path", sa.String(1024), nullable=False),
        sa.Column("break_probability", sa.Float(), nullable=False),
        sa.Column("node_importance", sa.Float(), server_default="0"),
        sa.Column("rank", sa.Integer(), nullable=False),
        sa.Column("explanation", sa.Text(), nullable=True),
    )

    op.create_table(
        "prediction_explanations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("prediction_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("predictions.id"), unique=True),
        sa.Column("root_cause", sa.Text(), server_default=""),
        sa.Column("risk_explanation", sa.Text(), server_default=""),
        sa.Column("affected_files_explanation", sa.Text(), server_default=""),
        sa.Column("reviewer_explanation", sa.Text(), nullable=True),
        sa.Column("attention_summary", postgresql.JSONB(), server_default="{}"),
    )

    op.create_table(
        "graph_snapshots",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("repository_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("repositories.id")),
        sa.Column("commit_sha", sa.String(40), nullable=False),
        sa.Column("node_count", sa.Integer(), server_default="0"),
        sa.Column("edge_count", sa.Integer(), server_default="0"),
        sa.Column("storage_path", sa.String(1024), server_default=""),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()")),
    )

    op.create_table(
        "graph_nodes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("snapshot_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("graph_snapshots.id")),
        sa.Column("node_id", sa.String(512), nullable=False),
        sa.Column("node_type", sa.String(50), nullable=False),
        sa.Column("name", sa.String(512), nullable=False),
        sa.Column("file_path", sa.String(1024), nullable=True),
        sa.Column("properties", postgresql.JSONB(), server_default="{}"),
    )

    op.create_table(
        "graph_edges",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("snapshot_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("graph_snapshots.id")),
        sa.Column("source_id", sa.String(512), nullable=False),
        sa.Column("target_id", sa.String(512), nullable=False),
        sa.Column("edge_type", sa.String(50), nullable=False),
        sa.Column("weight", sa.Float(), server_default="1.0"),
        sa.Column("properties", postgresql.JSONB(), server_default="{}"),
    )

    op.create_table(
        "issues",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("repository_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("repositories.id")),
        sa.Column("external_id", sa.String(100), nullable=False),
        sa.Column("title", sa.String(512), server_default=""),
        sa.Column("state", sa.String(50), server_default="open"),
        sa.Column("issue_type", sa.String(50), server_default="bug"),
        sa.Column("linked_commit_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("commits.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()")),
    )

    op.create_table(
        "embeddings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("repository_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("repositories.id")),
        sa.Column("entity_type", sa.String(50), nullable=False),
        sa.Column("entity_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("model_name", sa.String(255), nullable=False),
        sa.Column("dimension", sa.Integer(), nullable=False),
        sa.Column("qdrant_point_id", sa.String(100), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()")),
    )

    op.create_table(
        "reviewer_profiles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id")),
        sa.Column("repository_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("repositories.id")),
        sa.Column("expertise_area", sa.String(255), server_default=""),
        sa.Column("ownership_score", sa.Float(), server_default="0"),
        sa.Column("file_ownership_map", postgresql.JSONB(), server_default="{}"),
    )

    op.create_table(
        "sync_jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("repository_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("repositories.id")),
        sa.Column("status", sa.String(50), server_default="queued"),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("stats", postgresql.JSONB(), server_default="{}"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()")),
    )


def downgrade() -> None:
    for table in [
        "sync_jobs", "reviewer_profiles", "embeddings", "issues",
        "graph_edges", "graph_nodes", "graph_snapshots",
        "prediction_explanations", "affected_file_predictions", "predictions",
        "pull_requests", "commits", "ml_models", "repositories", "users",
    ]:
        op.drop_table(table)
