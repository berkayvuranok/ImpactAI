# Step 3: Dependency Graph Builder

## Overview

Step 3 builds **multi-layer dependency graphs** from repository source code at a specific commit. These graphs are the primary structural input for the GNN (Step 5).

## Graph Model

```mermaid
flowchart TB
    subgraph Node Types
        F[FILE]
        C[CLASS]
        FN[FUNCTION]
        M[MODULE]
        S[SERVICE]
    end

    subgraph Edge Types
        I[IMPORT]
        CALL[CALL]
        INH[INHERITANCE]
        COMP[COMPOSITION]
        API[API_CALL]
        DB[DATABASE_ACCESS]
        MQ[MESSAGE_QUEUE]
        MS[MICROSERVICE]
    end

    F -->|COMPOSITION| C
    C -->|COMPOSITION| FN
    F -->|IMPORT| M
    F -->|IMPORT| F
    FN -->|CALL| FN
    C -->|INHERITANCE| C
    F -->|API_CALL| S
    F -->|DATABASE_ACCESS| S
    F -->|MESSAGE_QUEUE| S
```

## Components

| Component | Path | Role |
|-----------|------|------|
| StructureAnalyzer | `infrastructure/analysis/structure_analyzer.py` | Calls, inheritance, external deps |
| DependencyGraphBuilder | `infrastructure/graph/dependency_graph_builder.py` | Full graph construction |
| GraphStorage | `infrastructure/graph/graph_storage.py` | JSON snapshot persistence |
| SubgraphExtractor | `infrastructure/graph/subgraph_extractor.py` | BFS for affected-file views |
| GraphBuildService | `application/services/graph_build_service.py` | Orchestration + DB persist |
| SqlAlchemyGraphRepository | `infrastructure/persistence/repositories.py` | PostgreSQL storage |

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/graph/{repository_id}` | Latest graph snapshot |
| GET | `/api/v1/graph/{repository_id}/{commit_sha}` | Graph at commit |
| GET | `/api/v1/graph/{repository_id}/subgraph?files=a.py&files=b.py` | BFS subgraph |
| POST | `/api/v1/graph/{repository_id}/build?commit_sha=...` | Build synchronously |
| POST | `/api/v1/graph/{repository_id}/build?commit_sha=...&async_build=true` | Queue Celery job |

## Pipeline

```mermaid
sequenceDiagram
    participant Sync as Repository Sync
    participant Celery
    participant Git
    participant Builder
    participant DB
    participant Disk

    Sync->>Celery: build_graph_task(head_sha)
    Celery->>Git: list_source_files + get_file_content
    Celery->>Builder: build_from_repository
    Builder->>DB: save_snapshot (nodes + edges)
    Builder->>Disk: JSON backup
```

After every successful repository sync, a graph build is automatically queued for `head_sha`.

## Node ID Convention

```
file:path/to/file.py
class:path/to/file.py:ClassName
function:path/to/file.py:qualified.name
module:app.service
service:api:httpx
```

## Testing

Run: `PYTHONPATH=src:tests pytest tests/unit/graph/ -v`

## Next Step

Step 4: Vector Embedding Service + Qdrant — embed commits, files, and graph nodes for similarity search.
