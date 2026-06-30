# Database Design

## Entity Relationship Diagram

```mermaid
erDiagram
    users ||--o{ repositories : owns
    users ||--o{ predictions : creates
    users ||--o{ reviewer_profiles : has
    repositories ||--o{ commits : contains
    repositories ||--o{ pull_requests : contains
    repositories ||--o{ graph_snapshots : has
    repositories ||--o{ sync_jobs : has
    commits ||--o{ file_changes : includes
    pull_requests ||--o{ predictions : triggers
    pull_requests ||--o{ pr_reviews : has
    predictions ||--o{ affected_file_predictions : includes
    predictions ||--o{ prediction_explanations : has
    predictions ||--o{ similar_commits : references
    graph_snapshots ||--o{ graph_nodes : contains
    graph_snapshots ||--o{ graph_edges : contains
    issues ||--o{ issue_labels : has
    commits ||--o| issues : fixes
    ml_models ||--o{ predictions : used_by
    embeddings }o--|| repositories : scoped_to

    users {
        uuid id PK
        string email UK
        string username UK
        string hashed_password
        string role
        boolean is_active
        timestamp created_at
    }

    repositories {
        uuid id PK
        uuid owner_id FK
        string name
        string url
        string default_branch
        string provider
        jsonb settings
        timestamp last_synced_at
        timestamp created_at
    }

    commits {
        uuid id PK
        uuid repository_id FK
        string sha UK
        string message
        string author_email
        timestamp committed_at
        boolean is_regression
        boolean is_rollback
        jsonb metadata
    }

    pull_requests {
        uuid id PK
        uuid repository_id FK
        int pr_number
        string title
        string state
        string head_sha
        string base_sha
        jsonb diff_stats
        timestamp created_at
        timestamp merged_at
    }

    predictions {
        uuid id PK
        uuid repository_id FK
        uuid pull_request_id FK
        uuid created_by FK
        uuid model_id FK
        string status
        float risk_score
        float regression_probability
        float confidence_score
        jsonb input_payload
        jsonb output_payload
        timestamp created_at
        timestamp completed_at
    }

    affected_file_predictions {
        uuid id PK
        uuid prediction_id FK
        string file_path
        float break_probability
        float node_importance
        int rank
    }

    graph_snapshots {
        uuid id PK
        uuid repository_id FK
        string commit_sha
        int node_count
        int edge_count
        string storage_path
        timestamp created_at
    }

    graph_nodes {
        uuid id PK
        uuid snapshot_id FK
        string node_id
        string node_type
        string name
        string file_path
        jsonb properties
    }

    graph_edges {
        uuid id PK
        uuid snapshot_id FK
        string source_id
        string target_id
        string edge_type
        float weight
        jsonb properties
    }

    issues {
        uuid id PK
        uuid repository_id FK
        string external_id
        string title
        string state
        string issue_type
        uuid linked_commit_id FK
        timestamp created_at
    }

    embeddings {
        uuid id PK
        uuid repository_id FK
        string entity_type
        uuid entity_id
        string model_name
        int dimension
        string qdrant_point_id
        timestamp created_at
    }

    ml_models {
        uuid id PK
        string name
        string version
        string model_type
        string artifact_path
        jsonb metrics
        boolean is_active
        timestamp trained_at
    }

    reviewer_profiles {
        uuid id PK
        uuid user_id FK
        uuid repository_id FK
        string expertise_area
        float ownership_score
        jsonb file_ownership_map
    }
```

## Indexing Strategy

- `commits(repository_id, sha)` — unique composite
- `predictions(repository_id, created_at DESC)` — history queries
- `graph_nodes(snapshot_id, node_type, file_path)` — graph lookups
- `embeddings(entity_type, entity_id)` — deduplication
- Partial index on `predictions(status)` WHERE status = 'pending'

## CQRS Read Models

| Read Model | Source Tables | Purpose |
|------------|---------------|---------|
| `prediction_summary_view` | predictions + affected_files | Dashboard list |
| `repository_risk_view` | predictions aggregated | Heatmap |
| `reviewer_expertise_view` | reviewer_profiles + graph_nodes | Reviewer ranking |
